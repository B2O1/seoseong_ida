# 서성이다 / Seoseong_ida

## 1. Overview

### 프로젝트 소개
- 서울의 수많은 카페들 중 원하는 카페를 쉽게 찾기 위한 웹사이트 개발

#### 설명
- 밤샘 카페, 카공 카페 같이 콘센트가 많거나 자리가 좋은, 새벽까지 하는 카페를 찾기 위해서 출발한 프로젝트
- 그 결과로 다양한 카테고리를 분류하여 사람들의 니즈를 충족하는 카페 분류
- 직접 크롤링한 데이터와 점수 계산 후 카테고리 분류
- Ollama를 이용한 챗봇 서비스 개발, 원하는 카페를 챗봇 형식으로 찾는 방식

#### 기대 효과
|항목|내용|
|---|---|
|편리성|사람들이 자신의 니즈에 맞게 더욱 쉽게 카페를 찾을 수 있음|
|신뢰성|가게 주인이 등록해놓은 '카페' 분류가 아닌 리뷰, 별점, 카테고리, 주소 등을 비교한 커피를 팔고 디저트를 파는 카페들의 분류 (공방 제외)|

## 2. 팀원 소개
|김혜원|박찬우|변해민|
|---|---|---|
|사진|![Image](https://github.com/user-attachments/assets/222eff0a-7a2a-455a-b4c0-50f011eccd56)|사진|

## 3. 프로젝트 기간 및 수행 내용
|기간|수행 내용|
|---|---|
|2025.03.03 ~ 2025.03.31|Django WorkFrame 공부, Figma 작성, UI 구현|
|2025.04.01 ~ 2025.05.21|공공데이터 전처리, 네이버 지도 크롤링, 크롤링된 데이터 전처리 및 가공|
|2025.05.21 ~ 2025.06.04| 크롤링 데이터 시각화 및 카테고리 분류 |
|2025.06.04 ~ 2025.06.11| 리뷰 데이터 분석 |
|2025.06.11 ~ 2025.06.25| UI 수정 및 기능 구현, django/mysql 연동|
|2025.07.21 ~ 2025.10.31| API 연동, Chatbot 서비스 개발 |
|2025.11.01 ~ 2025.12.31| AWS 연동 및 배포 관련 버그 픽스 |
|2026.01.01 ~ 현재| 퍼널 설계 및 분석 |

## 4. 프로젝트 환경 및 구성 요소

### Tech stack
|항목|내용|
|---|---|
|워크프레임|  <img src="https://img.shields.io/badge/django-092E20?style=for-the-badge&logo=django&logoColor=white"> 
|
|프로그램| <img src="https://img.shields.io/badge/googlecolab-F9AB00?style=for-the-badge&logo=googlecolab&logoColor=white"> <img src="https://img.shields.io/badge/mysql-4479A1?style=for-the-badge&logo=mysql&logoColor=white"> <img src="https://img.shields.io/badge/ananconda-44A833?style=for-the-badge&logo=anaconda&logoColor=white"> <img src="https://img.shields.io/badge/visualstudiocode-3776AB?style=for-the-badge&logo=visualstudiocode&logoColor=white">
|
|언어| <img src="https://img.shields.io/badge/javascript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=white"> <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">   <img src="https://img.shields.io/badge/css-663399?style=for-the-badge&logo=css&logoColor=white">  <img src="https://img.shields.io/badge/html5-E34F26?style=for-the-badge&logo=html5&logoColor=white">  
| 

## 5. 프로젝트 내용

단순하게 검색해서 카페를 찾는 것이 아닌 사용자의 상황과 목적에 맞는 카페를 찾을 수 있도록 설계한 데이터 기반 웹 서비스입니다.

### 프로젝트 개발 과정
1. 서울 공공데이터를 활용하여 데이터 다운로드
2. 활용 목적에 맞게 전처리 
3. Selenium을 이용한 Naver Map 크롤링을 진행
4. 수집한 데이터를 통하여 서성이다에 사용할 목적에 맞게 전처리
5. Django 프레임을 사용하여 HTML, CSS, JavaScript, MySQL, Python 프로그래밍 언어로 웹사이트 구현
6. 각종 API 연결 및 연동 (Naver, Firebase, Google)
7. Chatbot 모델 학습 및 구현
8. AWS EC2 연결, 배포 후 버그 픽스

### 프로젝트 개발 시 고민한 점
- 크롤링 데이터의 신뢰성과 활용 가능성
- 서비스 목적에 맞는 카페 카테고리 기준 재정의
- 동기/비동기 처리 관련 페이지 로딩 시간
- 확장과 유지보수를 고려한 UI 컴포넌트, 페이지, CSS 분리
- 사용자 경험을 고려한 페이지 설계

서성이다(Seoseong_ida)는 밤샘, 카공, 혼카 등 사용자의 상황과 목적에 맞는 카페를 찾기 위해 개발한 서울 카페 추천 웹 서비스입니다.
서울 공공데이터와 Selenium 기반 네이버 지도 크롤링으로 직접 수집·전처리한 데이터를 바탕으로 카페 점수를 계산하고 카테고리를 분류하였으며, Django와 MySQL을 활용해 웹 서비스로 구현했습니다.
또한 API 연동과 Ollama 기반 챗봇 기능을 통해 카페 탐색 방식을 확장하고, 동기·비동기 처리와 UI 컴포넌트 분리를 고려해 확장성과 유지보수성을 갖춘 구조로 설계했습니다.

## 6. 프로젝트를 마친 소감
|팀원|소감|
|---|---|
|김혜원| 작성 예정 |
|박찬우| 데이터 수집 및 분석, 사용 목적에 맞는 전처리가 어려웠다. 처음에는 잘 진행했다고 생각했으나 Django로 사용하려고 하니 데이터 형식이 안 맞았고 계속 수정했던 기억이 있다. 또한 웹사이트 model, view를 대부분 코딩했던 나로써 더욱 명확하게 설계를 하고 요구사항을 작성한 후에 만들어야한다는 것을 깨달았다. 결국 제일 중요한 것은 단순히 코딩을 하는 것보다 원하는 것을 제대로 인지하고 하나하나 따져본 후에 코드를 짜는 것이다. 수많은 버그 픽스와 의도와 다른 코딩으로 인하여 수많은 시간을 낭비하는 일이 없도록... |
|변해민| 작성 예정 |
