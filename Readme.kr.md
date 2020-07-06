## 프로젝트 개요: 스마트 팩토리용 설비 모니터링

스마트 팩토리용 오픈소스 모니러링 시스템인 WhaleShark IIoT는 IIoT기반 공정 모니터링 시스템입니다.
 - 모니터링 대상
   - 각종 환경 센서가 연결된 공정 설비 및 특정 사물
   - 공장 관리자로써 설비에 설치된 각종 센서값을 확인하여 설비의 상태를 실시간으로 모니터링 할 수 있습니다.
   
## Documents
 - [Document Home] 7월 초 공개 예정

## Download
 - [최신 Release](https://github.com/dataignitelab/WhaleShark_IIoT)

## 모듈
### WhaleShark IIoT는 4가지 주요 모듈로 구성된다 :
- 센서 수집용 임베디드 시스템 : 설비에 연결된 센서 값을 읽어 RS485를 통해 게이트웨이로 전달합니다.
- 게이트웨이 : 수집된 센서 값을 클라우드 서버의 에이전트로 전송합니다.
- 게이트웨이 에이전트 : 게이트웨이를 통해 전달된 Modbus기반 데이터를 보기 쉬운 데이터로 변환합니다.
- TSDB 에이전트 : 게이트웨이 에이전트에서 센서 값을 받아 TSDB에 저장합니다.

## Facebook
 - [WhaleShark IIoT 개발자 사용자 모임 - Facebook 그룹](생성 예정입니다.)

## WhaleShark IIoT에 기여하기
 - **Pull request**는 반드시 **develop branch**로 요청하여야 합니다.
 - 상세한 내용은 Blog를 참조하여 사 학습하시기 바랍니다.
   - https://blog.naver.com/PostList.nhn?blogId=dataignitelab&categoryNo=6
   
## WhaleShark IIoT 개발 방법
- 센서 수집용 임베디드 시스템 : RT-OS인 RT-Thread를 이용합니다.(.https://github.com/RT-Thread/rt-thread)
- 게이트웨이 : 7월 초 공개 예정
- 게이트웨어 에이전트:  7월 초 공개 예정

## License
Licensed under the Apache License, Version 2.0
<br>
