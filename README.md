# 📱 CodeQuest 백엔드 서버

> **React Native 앱을 위한 API 서버**  
> 프론트엔드에서 요청하면, 데이터를 JSON으로 돌려주는 역할만 합니다!

---

## 🎯 이 서버가 하는 일

```
React Native 앱 → "데이터 주세요!" → Django 서버 → "여기 있어요!" 
                                          ↓
                                      MariaDB
```

**간단히 말하면:**
- ✅ 앱에서 필요한 데이터를 조회해서 전달
- ✅ 데이터를 JSON 형태로 제공
- ❌ 화면(HTML)은 만들지 않음
- ❌ 직접 데이터 수정은 불가 (읽기 전용)

---

## 🌐 서버 주소

- **메인 도메인**: `https://codequest.co.kr`
- **API 테스트**: `https://codequest.co.kr/api/test/`
- **API 문서**: `https://codequest.co.kr/api/docs/` (Swagger UI)
- **관리자 페이지**: `https://codequest.co.kr/admin/`

---

## 🔌 API 사용 방법

### React Native에서 호출 예시

```javascript
// 데이터 가져오기
fetch('https://codequest.co.kr/api/test/')
  .then(response => response.json())
  .then(data => {
    console.log(data); // 서버에서 받은 데이터
  });
```

### 응답 형태

```json
{
  "message": "서버에서 보낸 메시지",
  "data": {
    "id": 1,
    "title": "제목",
    "content": "내용"
  }
}
```

---

## 🏗️ 서버 구조

```
[ 사용자의 앱 ]
      ↓
[ Cloudflare ] ← 보안 & 속도 향상
      ↓
[ Nginx ] ← 트래픽 관리
      ↓
[ Django (Gunicorn) ] ← 실제 API 처리
      ↓
[ MariaDB ] ← 데이터 저장소
```

### 각 역할 설명
- **Cloudflare**: 해외 접속 차단, DDoS 방어, 빠른 속도
- **Nginx**: 요청을 Django로 전달하는 문지기
- **Django**: 실제 로직 처리 & API 제공
- **MariaDB**: 모든 데이터 저장

---

## 🔒 보안 설정

### 1. HTTPS 암호화
- 모든 통신이 암호화되어 전송됩니다
- 앱 ↔ 서버 간 데이터 도청 불가능

### 2. 한국에서만 접속 가능
- Cloudflare에서 해외 IP 자동 차단
- 한국(KR)에서만 서버 접근 가능

### 3. 읽기 전용 API
- 데이터 조회만 가능
- 수정/삭제는 관리자만 가능

---

## 📦 주요 기능

### 현재 제공 중인 API

Swagger UI에서 모든 API를 테스트하고 확인할 수 있습니다:
👉 **https://codequest.co.kr/api/docs/**

- `/api/test/` - 서버 연결 테스트
- 새로운 내용 추가되면 여기에 작성 부탁드립니다!
---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| **언어** | Python 3.x |
| **프레임워크** | Django 5.2.7 |
| **API** | Django REST Framework |
| **데이터베이스** | MariaDB |
| **서버** | AWS EC2 (Ubuntu 24.04) |
| **웹서버** | Nginx + Gunicorn |
| **보안/CDN** | Cloudflare |
| **도메인** | codequest.co.kr |

---

## 📱 프론트엔드 개발자를 위한 가이드

### ✅ 해야 할 것
- API 엔드포인트로 요청 보내기
- JSON 응답 받아서 처리하기
- HTTPS 사용하기

### ❌ 하지 말아야 할 것
- 직접 데이터베이스 접근
- HTTP(비암호화) 사용
- API 문서에 없는 엔드포인트 호출

---

## 🚀 배포 정보

### 서버 위치
- **클라우드**: AWS 서울 리전
- **서버 타입**: EC2 t3.micro (프리티어)
- **운영체제**: Ubuntu 24.04 LTS

### 운영 시간
- **24시간 365일** 운영
- 자동 재시작 설정 완료

---

## 🔄 업데이트 프로세스

### 코드 업데이트 시
```bash
# 1. 로컬에서 푸시
git push origin main

# 2. 서버에서 풀
git pull origin main

# 3. 서버 재시작
sudo systemctl restart gunicorn
```

⏱️ **예상 시간**: 약 1-2분  
🔄 **다운타임**: 거의 없음 (재시작 동안만 잠깐)

---

## 💡 자주 묻는 질문

### Q. API는 무료인가요?
**A.** 네, 현재는 무료입니다. (AWS 프리티어 사용 중)

### Q. 데이터는 어떻게 추가하나요?
**A.** Django Admin 페이지에서 관리자가 추가합니다.

### Q. 앱에서 데이터 수정이 필요하면?
**A.** 현재는 조회만 가능합니다. 추후 인증 시스템 추가 후 수정 API 제공 예정입니다.

### Q. 서버가 다운되면?
**A.** 자동 재시작 설정이 되어있어 대부분 자동 복구됩니다. 문제 시 팀에 연락 주세요.

### Q. 새로운 API가 필요하면?
**A.** Swagger 문서를 확인하시고, 없으면 백엔드 팀에 요청해주세요.

---

## 📞 문제 발생 시

### 1. API가 응답하지 않을 때
- Swagger UI에서 테스트해보세요
- 서버 상태 확인: `https://codequest.co.kr/api/test/`

### 2. 에러 메시지를 받았을 때
- 에러 메시지와 함께 백엔드 팀에 전달
- API 문서에서 올바른 요청 형식 확인

### 3. 연락처
- GitHub Issues에 등록
- 또는 팀 채널로 문의

---

## 🎯 요약

| 항목 | 내용 |
|------|------|
| **서버 역할** | React Native 앱을 위한 데이터 제공 |
| **접근 방법** | HTTPS API 호출 |
| **주요 기능** | 데이터 조회 (읽기 전용) |
| **문서** | Swagger UI |
| **보안** | HTTPS + 한국 IP만 허용 |
| **가용성** | 24/7 운영 |

---

## 🔗 빠른 링크

- 📡 [API 테스트](https://codequest.co.kr/api/test/)
- 📚 [API 문서 (Swagger)](https://codequest.co.kr/api/docs/)
- 🔧 [관리자 페이지](https://codequest.co.kr/admin/)
- ☁️ [Cloudflare 대시보드](https://dash.cloudflare.com)

---

**이 서버는 여러분의 앱에 날개를 달아줍니다!** 🚀

궁금한 점이 있으면 언제든 물어보세요!
