// 즉시실행함수(IIFE)로 감싸서 전역 오염 방지
var CoffeePlaces = (function() {
  // 1) 검색할 키워드 목록
  var keywords = [
    '달콤상자별','컴투레스트', '클라이네스', '디오티 충무로점', '목단가옥', '테오마', 'sym', 'cup&coffee',
       'Cafe헤븐', '리스트레토2010', '까루나', '롱앤쇼트', '달콤놀이터', '고팡커피', '달콤상자별',
       '효선CAS', '메이커스유니온스퀘어'
    // '커피베이 청량리점',
    // '이디야커피 답십리파크자이점'
    // 추가 가능
  ];
  
  // 내부 상태 변수
  var map, ps, infowindow, bounds;
  
  // 2) 초기화 함수: containerId와 옵션을 받음
  function init(containerId, centerLatLng, zoomLevel, delay) {
    // 지도 생성
    map = new kakao.maps.Map(
      document.getElementById(containerId),
      { center: centerLatLng, level: zoomLevel }
    );
    infowindow = new kakao.maps.InfoWindow({ zIndex: 1 });
    ps = new kakao.maps.services.Places();
    bounds = new kakao.maps.LatLngBounds();
    
    // 키워드별로 검색 실행
    keywords.forEach(function(keyword, idx) {
      setTimeout(function() {
        ps.keywordSearch(keyword, placesSearchCB);
      }, (delay||300) * idx);
    });
  }
  
  // 3) 검색 콜백
  function placesSearchCB(data, status, pagination) {
    if (status === kakao.maps.services.Status.OK) {
      data.forEach(function(place) {
        _displayMarker(place);
        bounds.extend(new kakao.maps.LatLng(place.y, place.x));
      });
      map.setBounds(bounds);
    }
  }
  
  // 4) 마커 표시
  function _displayMarker(place) {
    var marker = new kakao.maps.Marker({
      map: map,
      position: new kakao.maps.LatLng(place.y, place.x)
    });
    kakao.maps.event.addListener(marker, 'click', function() {
      var url = 'https://place.map.kakao.com/' + place.id;
      infowindow.setContent(
        '<div style="padding:5px;font-size:12px;">' +
          '<a href="' + url + '" target="_blank">' +
            place.place_name +
          '</a>' +
        '</div>'
      );
      infowindow.open(map, marker);
    });
  }
  
  // 외부에 노출할 API
  return {
    init: init
  };
  
})();