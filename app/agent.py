# app/agent.py

from typing import TypedDict, Dict, Any, List, Optional
import json
import requests
import pymysql
from langgraph.graph import StateGraph, END

# 여기서 네가 말한 categories_json 파일을 import
# app/categories_json.py 안에 categories_json 이라고 정의되어 있다고 가정
from .categories_json import categories_json


# ============================================================
# 1. 카테고리 한글 → DB 실제 컬럼 매핑
#    (categories_json 의 code 기준으로 맞춰줌)
# ============================================================

KOR2COL = {
    "쾌좋카": "comfy_cafe",
    "혼좋카": "solo_cafe",
    "책좋카": "book_cafe",
    "이걸안카": "unique_cafe",
    "단좋카": "group_cafe",
    "커맛카": "coffee_taste_cafe",
    "카공카": "study_cafe",
    "화청카": "bright_cafe",
    "분좋카": "mood_cafe",
    "디맛카": "dessert_taste_cafe",
    "가좋카": "cheap_cafe",
    "반동카": "animal_cafe",
    "밤샘카": "night_cafe",   # ← categories_json code 기준
    "한옼카": "hanok_cafe",   # ← 네 파일에 '한옼카'로 되어있어서 코드에 맞춤
}


# ============================================================
# 2. LangGraph State 정의
# ============================================================

class State(TypedDict, total=False):
    user_query: str
    slots: Dict[str, Any]          # {"who": [...], "where": "...", ...}
    category: str                  # "카공카" 등
    plan: Dict[str, Any]           # planner가 만든 계획용 JSON
    sql: str
    db_results: List[Dict[str, Any]]
    error: Optional[str]
    need_retry: bool
    retry_count: int
    final_answer: str


# ============================================================
# 3. Planner LLM (Ollama llama3.2:3b)
# ============================================================

def call_planner_llm(user_query: str) -> Dict[str, Any]:
    """
    Ollama llama3.2:3b 모델을 호출해서
    - who, what, where, special, category, location_normalized 를 JSON으로 추출하는 함수
    """
    system_prompt = f"""
너는 카페 검색을 위한 질의 분석 에이전트다.

아래는 우리가 정의한 카페 카테고리 JSON이다. (카테고리는 code 필드로 구분된다.)

{categories_json}

사용자의 질문을 읽고 다음 정보를 JSON 형식으로만 출력해라.

1. who: 사람/관계 (친구, 연인, 가족, 혼자, 직장 동료 등) 리스트
2. what: 목적/분위기/활동 (조용함, 공부, 사진, 분위기 좋은, 감성, 디저트, 커피, 가성비 등) 리스트
3. where: 위치/지역명 (예: 연남동, 합정, 성수, 제주 등) 문자열
4. special: '콘센트', '24시간', '반려동물', '한옥', '테라스', '야외석', '뷰 좋은' 등 특별 조건 리스트
5. location_normalized: 
   사용자가 말한 지역명이 '동' 또는 상권명(예: 연남동, 연희동, 성수, 홍대 등)인 경우,
   한국 행정구역 지식을 바탕으로 해당 지역이 포함된 '구' 단위 행정구역명을 넣어라.
   예: 연남동 -> 마포구, 연희동 -> 서대문구, 성수동 -> 성동구, 서교동 -> 마포구
   만약 이미 '마포구', '성동구'처럼 구 단위로 말한 경우 그대로 사용해도 된다.
6. category: 위의 정보와 카테고리 정의 JSON을 참고하여 가장 적합한 카테고리 code 하나 (예: "카공카", "분좋카", "디맛카" 등)

반드시 아래 JSON 형식 그대로만 출력해라. 설명 문장은 쓰지 마라.

예시 형식:
{{
  "who": [],
  "what": [],
  "where": "",
  "special": [],
  "location_normalized": "",
  "category": ""
}}

사용자 질문:
\"{user_query}\"
"""

    payload = {
        "model": "llama3.2:3b",
        "prompt": system_prompt,
        "stream": False,
    }

    res = requests.post("http://localhost:11434/api/generate", json=payload)
    res.raise_for_status()
    text = res.json()["response"].strip()

    # LLM 응답에서 JSON만 뽑는 헬퍼
    def extract_json(s: str) -> Dict[str, Any]:
        try:
            return json.loads(s)
        except Exception:
            pass
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            sub = s[start:end+1]
            return json.loads(sub)
        raise ValueError(f"LLM 출력에서 JSON을 파싱할 수 없습니다: {s}")

    data = extract_json(text)

    # 기본값 정리
    for key in ["who", "what", "special"]:
        if key not in data or not isinstance(data[key], list):
            data[key] = []
    if "where" not in data or not isinstance(data["where"], str):
        data["where"] = ""
    if "category" not in data or not isinstance(data["category"], str):
        data["category"] = ""
    if "location_normalized" not in data or not isinstance(data["location_normalized"], str):
        data["location_normalized"] = ""

    return data


# ============================================================
# 4. MySQL 쿼리 함수
# ============================================================

def run_query(sql: str, params=None) -> List[Dict[str, Any]]:
    conn = pymysql.connect(
        host="localhost",
        user="root",
        password="0000",      # 나중에 settings에서 가져와도 좋음
        database="myproject_db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
    finally:
        conn.close()


# ============================================================
# 5. LangGraph 노드 구현
# ============================================================

# 5-1. Planner 노드
def planner_node(state: State) -> State:
    user_query = state["user_query"]

    parsed = call_planner_llm(user_query)

    slots = {
        "who": parsed.get("who", []),
        "what": parsed.get("what", []),
        "where": parsed.get("where", ""),
        "special": parsed.get("special", []),
        "location_normalized": parsed.get("location_normalized", ""),
    }
    category = parsed.get("category", "")

    # 카테고리가 비어 있으면 간단한 규칙으로 fallback
    if not category:
        text = " ".join(slots["what"] + slots["special"])
        if any(k in text for k in ["공부", "과제", "콘센트", "노트북", "작업"]):
            category = "카공카"
        else:
            category = "쾌좋카"

    plan = {
        "action": "query_cafe_by_category",
        "area": slots["where"],
        "category": category,
    }

    state["slots"] = slots
    state["category"] = category
    state["plan"] = plan
    state["retry_count"] = state.get("retry_count", 0)
    return state


# 5-2. Executor 노드
def executor_node(state: State) -> State:
    plan = state["plan"]
    category = state["category"]
    slots = state["slots"]

    dong = slots.get("where", "")                     # 예: "연희동"
    gu = slots.get("location_normalized", "")         # 예: "서대문구"
    use_gu_only = slots.get("use_gu_only", False)     # Reflexion에서 설정하는 플래그

    col = KOR2COL.get(category)

    if not col:
        state["error"] = f"Unknown category: {category}"
        state["db_results"] = []
        return state

    # DISTINCT: 같은 카페 중복 제거
    sql = f"""
        SELECT DISTINCT crawled_store_name, address, rating
        FROM df_cafe_full
        WHERE {col} = 1
    """
    params: List[Any] = []

    # 1차: 동 키워드, 2차: 구 키워드
    if dong and not use_gu_only:
        dong_keyword = dong.replace("동", "")  # "연희동" -> "연희"
        sql += " AND address LIKE %s"
        params.append(f"%{dong_keyword}%")
    elif gu:
        sql += " AND address LIKE %s"
        params.append(f"%{gu}%")

    sql += " ORDER BY rating DESC LIMIT 10"

    try:
        results = run_query(sql, params)
        state["sql"] = sql
        state["db_results"] = results
        state["error"] = None
    except Exception as e:
        state["db_results"] = []
        state["error"] = str(e)

    return state


# 5-3. Observer 노드
def observer_node(state: State) -> State:
    results = state.get("db_results", [])
    error = state.get("error")
    retry_count = state.get("retry_count", 0)

    state["need_retry"] = False

    if error:
        state["need_retry"] = retry_count < 1
        return state

    # 위치 완화(1번), 카테고리 완화(1번) → 총 2번까지 재시도
    if len(results) == 0 and retry_count < 2:
        state["need_retry"] = True

    return state


# 5-4. Reflexion 노드
def reflexion_node(state: State) -> State:
    category = state["category"]
    retry_count = state.get("retry_count", 0)
    slots = state.get("slots", {})

    gu = slots.get("location_normalized", "")

    # 첫 번째 재시도: gu가 있을 때만 동 -> 구로 완화
    if retry_count == 0 and gu:
        slots["use_gu_only"] = True
        state["slots"] = slots
        state["retry_count"] = retry_count + 1
        state["need_retry"] = False
        return state

    # gu가 없거나 이미 한 번 시도한 경우 → 카테고리 완화
    if category == "카공카":
        new_category = "쾌좋카"
    else:
        new_category = "분좋카"

    state["category"] = new_category
    if "plan" in state:
        state["plan"]["category"] = new_category
    state["retry_count"] = retry_count + 1
    state["need_retry"] = False
    return state


# 5-5. Finalizer 노드
def finalizer_node(state: State) -> State:
    results = state.get("db_results", [])
    category = state.get("category")
    slots = state.get("slots", {})

    dong = slots.get("where", "")
    gu = slots.get("location_normalized", "")
    use_gu_only = slots.get("use_gu_only", False)

    if not results:
        where_for_msg = dong or gu or ""
        state["final_answer"] = f"{where_for_msg}에서 {category} 조건에 맞는 카페를 찾지 못했어요."
        return state

    # 안내 문구
    if dong and use_gu_only and gu:
        prefix = f"'{dong}'에 딱 맞는 카페는 없어서, 대신 {gu} 전체에서 비슷한 카페를 추천할게요."
    elif dong:
        prefix = f"{dong} 근처에서 찾은 {category} 카페들이에요."
    elif gu:
        prefix = f"{gu}에서 찾은 {category} 카페들이에요."
    else:
        prefix = f"{category} 카페 추천 리스트에요."

    lines = [prefix]

    for r in results[:5]:
        name = r.get("crawled_store_name", "이름 없음")
        raw_rating = r.get("rating", "")
        cleaned_rating = (
            raw_rating.replace("별점", "").replace("\n", "").strip()
            if isinstance(raw_rating, str) else raw_rating
        )
        addr = r.get("address", "")
        lines.append(f"- {name} (★{cleaned_rating}) - {addr}")

    state["final_answer"] = "\n".join(lines)
    return state


# ============================================================
# 6. LangGraph 그래프 구성
# ============================================================

graph = StateGraph(State)

graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("observer", observer_node)
graph.add_node("reflexion", reflexion_node)
graph.add_node("finalizer", finalizer_node)

graph.set_entry_point("planner")
graph.add_edge("planner", "executor")
graph.add_edge("executor", "observer")


def route_from_observer(state: State) -> str:
    if state.get("need_retry", False):
        return "reflexion"
    else:
        return "finalizer"


graph.add_conditional_edges(
    "observer",
    route_from_observer,
    {
        "reflexion": "reflexion",
        "finalizer": "finalizer",
    },
)

graph.add_edge("reflexion", "executor")
graph.add_edge("finalizer", END)

app = graph.compile()


# ============================================================
# 7. Django에서 쓰기 좋은 래퍼 함수
# ============================================================

def run_cafe_agent(user_query: str) -> Dict[str, Any]:
    """
    Django view 에서:
        result = run_cafe_agent(request.POST["message"])
    이런 식으로 쓰려고 만든 helper
    """
    init_state: State = {
        "user_query": user_query
    }
    final_state = app.invoke(init_state)
    return {
        "answer": final_state.get("final_answer", "결과 없음"),
        "sql": final_state.get("sql", ""),
        "raw_results": final_state.get("db_results", []),
        "error": final_state.get("error"),
    }
