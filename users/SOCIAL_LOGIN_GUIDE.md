# 소셜 로그인 구현 가이드

## 📋 개요

CodeQuest 백엔드에서 소셜 로그인(OAuth2)을 구현한 가이드입니다.

지원하는 소셜 제공자:
- ✅ Google
- ✅ Kakao
- ✅ Naver
- 🚧 Apple (구현 예정)

---

## 🏗️ 구조

```
users/
├── social_auth.py         # 소셜 인증 로직 (각 제공자별 API 호출)
├── services.py            # 비즈니스 로직 (소셜 로그인 처리)
├── views.py               # API 엔드포인트 (요청/응답 처리)
├── models.py              # SocialAccount 모델
└── serializers/
    └── socialAccount_serializer.py  # 요청/응답 직렬화
```

### 파일별 역할

#### 1. `social_auth.py` - 소셜 인증 제공자
- 각 소셜 제공자(Google, Kakao, Naver)의 API 호출
- Access Token 검증
- 사용자 정보 추출 및 표준화

```python
# 사용 예시
provider = SocialAuthProvider.get_provider('google')
user_info = provider.get_user_info(access_token)
```

#### 2. `services.py` - 비즈니스 로직
- `social_login()` 메서드: 소셜 로그인 전체 플로우 처리
- 사용자 생성/조회
- JWT 토큰 발급
- Refresh Token 저장

#### 3. `views.py` - API 엔드포인트
- `SocialLoginView`: 소셜 로그인 API
- 요청 검증
- 응답 반환

#### 4. `models.py` - 데이터베이스 모델
- `SocialAccount`: 소셜 계정 정보 저장
- `find_or_create_user()`: 사용자 찾기/생성

---

## 🔌 API 사용 방법

### 엔드포인트

```
POST /auth/social/login/
```

### Request Body

```json
{
  "provider": "google",           // "google" | "kakao" | "naver"
  "access_token": "ya29.a0...",   // 소셜 제공자로부터 받은 Access Token
  "device_id": "device_123",      // 선택적: 디바이스 고유 ID
  "device_name": "iPhone 15"      // 선택적: 디바이스 이름
}
```

### Response (성공)

```json
{
  "success": true,
  "is_new_user": false,           // true면 신규 가입, false면 기존 사용자
  "access": "eyJ0eXAi...",        // JWT Access Token
  "refresh": "eyJ0eXAi...",       // JWT Refresh Token
  "user": {
    "user_id": "uuid...",
    "email": "user@gmail.com",
    "nickname": "사용자",
    "profile_image_url": "https://...",
    // ... 기타 사용자 정보
  }
}
```

### Response (실패)

```json
{
  "error": "소셜 로그인 실패: Google API 호출 실패"
}
```

---

## 🚀 프론트엔드 연동 가이드

### React Native (Expo) 예시

#### 1. Google 로그인

```javascript
import * as Google from 'expo-auth-session/providers/google';

// 1. Google 로그인 설정
const [request, response, promptAsync] = Google.useAuthRequest({
  expoClientId: 'YOUR_EXPO_CLIENT_ID',
  iosClientId: 'YOUR_IOS_CLIENT_ID',
  androidClientId: 'YOUR_ANDROID_CLIENT_ID',
  webClientId: 'YOUR_WEB_CLIENT_ID',
});

// 2. 로그인 버튼 클릭 시
const handleGoogleLogin = async () => {
  const result = await promptAsync();
  
  if (result?.type === 'success') {
    const accessToken = result.authentication.accessToken;
    
    // 3. 백엔드에 Access Token 전달
    const response = await fetch('http://192.168.0.24:8000/auth/social/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider: 'google',
        access_token: accessToken,
        device_id: await getDeviceId(),
        device_name: await getDeviceName(),
      }),
    });
    
    const data = await response.json();
    
    if (data.success) {
      // 4. JWT 토큰 저장
      await AsyncStorage.setItem('access_token', data.access);
      await AsyncStorage.setItem('refresh_token', data.refresh);
      
      // 5. 사용자 정보 저장
      await AsyncStorage.setItem('user', JSON.stringify(data.user));
      
      console.log('로그인 성공!', data.user);
    }
  }
};
```

#### 2. Kakao 로그인

```javascript
import * as KakaoLogin from '@react-native-seoul/kakao-login';

const handleKakaoLogin = async () => {
  try {
    // 1. Kakao SDK로 로그인
    const result = await KakaoLogin.login();
    
    // 2. 백엔드에 Access Token 전달
    const response = await fetch('http://192.168.0.24:8000/auth/social/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider: 'kakao',
        access_token: result.accessToken,
        device_id: await getDeviceId(),
        device_name: await getDeviceName(),
      }),
    });
    
    const data = await response.json();
    // ... 토큰 저장 로직
  } catch (error) {
    console.error('Kakao 로그인 실패:', error);
  }
};
```

#### 3. Naver 로그인

```javascript
import NaverLogin from '@react-native-seoul/naver-login';

const handleNaverLogin = async () => {
  try {
    // 1. Naver SDK로 로그인
    const result = await NaverLogin.login({
      appName: 'CodeQuest',
      consumerKey: 'YOUR_CONSUMER_KEY',
      consumerSecret: 'YOUR_CONSUMER_SECRET',
      serviceUrlScheme: 'codequest',
    });
    
    // 2. 백엔드에 Access Token 전달
    const response = await fetch('http://192.168.0.24:8000/auth/social/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider: 'naver',
        access_token: result.accessToken,
        device_id: await getDeviceId(),
        device_name: await getDeviceName(),
      }),
    });
    
    const data = await response.json();
    // ... 토큰 저장 로직
  } catch (error) {
    console.error('Naver 로그인 실패:', error);
  }
};
```

---

## 🔄 플로우 다이어그램

```
[ 프론트엔드 ]                    [ 백엔드 ]                 [ 소셜 제공자 ]
      |                                |                            |
      | 1. 소셜 로그인 요청              |                            |
      |-------------------------------->| Google/Kakao/Naver        |
      |                                |                            |
      | 2. 사용자 인증 페이지 표시        |                            |
      |<--------------------------------|                            |
      |                                |                            |
      | 3. 로그인 승인                   |                            |
      |---------------------------------------------------------------->|
      |                                |                            |
      | 4. Access Token 받음           |                            |
      |<----------------------------------------------------------------|
      |                                |                            |
      | 5. Access Token 전달           |                            |
      |-------------------------------->|                            |
      |                                |                            |
      |                                | 6. Token으로 사용자 정보 요청 |
      |                                |--------------------------->|
      |                                |                            |
      |                                | 7. 사용자 정보 응답           |
      |                                |<---------------------------|
      |                                |                            |
      |                                | 8. DB에서 사용자 찾기/생성    |
      |                                | 9. JWT 토큰 생성             |
      |                                |                            |
      | 10. JWT + 사용자 정보 응답       |                            |
      |<--------------------------------|                            |
      |                                |                            |
      | 11. 토큰 저장 & 로그인 완료      |                            |
```

---

## 🛠️ 개발자 노트

### 각 제공자별 특징

#### Google
- 가장 표준적인 OAuth2 구현
- Access Token으로 바로 사용자 정보 조회 가능
- 이메일 정보 항상 제공

#### Kakao
- 카카오계정 정보를 통해 사용자 정보 제공
- 이메일이 선택적으로 제공될 수 있음 (사용자 동의 필요)
- 이메일이 없으면 `kakao_{id}@codequest.app` 형식으로 생성

#### Naver
- resultcode로 성공 여부 확인 필요
- response 객체 안에 실제 사용자 정보 포함
- 다양한 추가 정보 제공 (나이, 성별, 생일 등)

#### Apple (구현 예정)
- JWT 토큰 검증 필요
- 최초 로그인 시에만 사용자 정보 제공
- 이후에는 저장된 정보 사용해야 함

---

## 🧪 테스트 방법

### 1. Swagger UI에서 테스트

```
http://localhost:8000/api/docs/
```

1. `/auth/social/login/` 엔드포인트 선택
2. Request Body 입력:
```json
{
  "provider": "google",
  "access_token": "실제_액세스_토큰",
  "device_id": "test_device",
  "device_name": "Test Device"
}
```
3. Execute 클릭

### 2. PowerShell에서 테스트

```powershell
$headers = @{ "Content-Type" = "application/json" }
$body = @{
    provider = "google"
    access_token = "실제_액세스_토큰"
    device_id = "test_device"
    device_name = "Test Device"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/auth/social/login/" `
    -Method POST `
    -Headers $headers `
    -Body $body
```

---

## ⚠️ 주의사항

### 보안

1. **Access Token은 절대 로그에 남기지 않기**
   ```python
   # ❌ 나쁜 예
   print(f"Access Token: {access_token}")
   
   # ✅ 좋은 예
   print(f"Access Token: {access_token[:10]}...")
   ```

2. **HTTPS 사용**
   - 프로덕션에서는 반드시 HTTPS 사용
   - Access Token이 네트워크를 통해 전송되므로 암호화 필수

3. **토큰 만료 처리**
   - Access Token은 일정 시간 후 만료됨
   - 프론트엔드에서 만료된 토큰 처리 로직 필요

### 에러 처리

소셜 로그인 실패 시 가능한 원인:
1. Access Token이 만료됨
2. 소셜 제공자 API 서버 장애
3. 네트워크 연결 문제
4. 잘못된 provider 이름

---

## 📚 참고 자료

- [Google OAuth2 문서](https://developers.google.com/identity/protocols/oauth2)
- [Kakao 로그인 REST API](https://developers.kakao.com/docs/latest/ko/kakaologin/rest-api)
- [Naver 로그인 API](https://developers.naver.com/docs/login/api/api.md)
- [Apple Sign In](https://developer.apple.com/documentation/sign_in_with_apple)

---

## 🔧 트러블슈팅

### "지원하지 않는 소셜 제공자입니다"
- `provider` 값이 올바른지 확인 ('google', 'kakao', 'naver' 중 하나)

### "Access Token이 유효하지 않습니다"
- Access Token이 만료되었거나 잘못된 값
- 소셜 제공자에서 새로운 토큰 받아서 재시도

### "이메일 정보를 가져올 수 없습니다"
- Google: 거의 발생하지 않음
- Kakao: 사용자가 이메일 제공 동의 안 함
- Naver: API 설정에서 이메일 권한 확인

---

## 📝 TODO

- [ ] Apple Sign In 구현
- [ ] Refresh Token 갱신 로직
- [ ] 소셜 계정 연결/해제 API
- [ ] 여러 소셜 계정 연동 지원
- [ ] 소셜 로그인 통계 및 로깅

---

**작성일**: 2025-10-29  
**작성자**: CodeQuest Team
