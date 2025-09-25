import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import axios from 'axios';

const LoginContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: #1a1a1a;
  color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
`;

const Logo = styled.h1`
  font-size: 48px;
  font-weight: bold;
  margin-bottom: 20px;
  color: #ffffff;
`;

const Subtitle = styled.p`
  font-size: 18px;
  color: #888;
  margin-bottom: 40px;
`;

const GoogleButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
  color: #333;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);

  &:hover {
    background: #f5f5f5;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }

  &:active {
    transform: translateY(1px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
`;

const GoogleIcon = styled.div`
  width: 20px;
  height: 20px;
  margin-right: 12px;
  background: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyMCAyMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwLjAwMDEgNC4xNjY2N0MxMS44MzM0IDQuMTY2NjcgMTMuNDE2NyA0LjgzMzMzIDE0LjU4MzQgNS45MTY2N0wxNy4wODM0IDMuNDE2NjdDMTUuMjUwMSAxLjY2NjY3IDEyLjU4MzQgMC41IDkuOTk5OTkgMC41QzYuNDE2NjcgMC41IDMuMjUwMDEgMi41ODMzMyAxLjI1MDAxIDUuNzQ5OTlMNC4wODMzNCA4LjA4MzMzQzUuNDE2NjcgNi4wODMzMyA3LjU4MzM0IDQuMTY2NjcgMTAuMDAwMSA0LjE2NjY3WiIgZmlsbD0iI0VBMjMzNiIvPgo8cGF0aCBkPSJNMTkuMTY2NyAxMC4yNUMxOS4xNjY3IDkuNTgzMzMgMTkuMDgzNCA4LjkxNjY3IDE4LjkxNjcgOC4zMzMzM0gxMFYzLjVIMi4wODMzNEMxLjA4MzM0IDYuMDgzMzMgMC41IDMuMDgzMzMgMC41IDAuNUgxMC4wMDAxQzE1LjUgMC41IDIwLjAwMDEgNC43NSAyMC4wMDAxIDEwLjI1WiIgZmlsbD0iIzQyODVGNCIvPgo8cGF0aCBkPSJNMTAgMjBDNy41ODMzNCAyMCA1LjI1MDAxIDE5LjA4MzMzIDMuNDE2NjcgMTcuNDE2NjdMMC41ODMzMzQgMTQuOTE2NjdDMi43NTAwMSAxNy40MTY2NyA2LjA4MzM0IDE5IDEwIDE5WiIgZmlsbD0iIzE0QTg1MyIvPgo8cGF0aCBkPSJNMTAgMjBDMTIuOTE2NyAyMCAxNS42NjY3IDE5LjA4MzMzIDE3LjkxNjcgMTcuNDE2NjdMMTQuNTgzNCAxNC45MTY2N0MxMy40MTY3IDE1LjkxNjY3IDExLjgzMzQgMTYuNSAxMCAxNi41QzcuNTgzMzQgMTYuNSA1LjI1MDAxIDE1LjQxNjY3IDMuNDE2NjcgMTMuNzVMMC41ODMzMzQgMTYuMjVDMi43NTAwMSAxOC43NSA2LjA4MzM0IDIwIDEwIDIwWiIgZmlsbD0iI0ZGQkMwNCIvPgo8L3N2Zz4K') no-repeat center;
  background-size: contain;
`;

const LoginPage = () => {
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Google OAuth2 스크립트 로드
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
      // Google OAuth2 초기화
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: process.env.REACT_APP_GOOGLE_CLIENT_ID || 'your-google-client-id',
          callback: handleGoogleResponse
        });
      }
    };

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  const handleGoogleResponse = async (response) => {
    setIsLoading(true);
    
    try {
      // Google OAuth2 응답 처리
      const backendResponse = await axios.post('/api/auth/google', {
        access_token: response.credential
      });
      
      // 토큰 저장
      localStorage.setItem('access_token', backendResponse.data.access_token);
      localStorage.setItem('refresh_token', backendResponse.data.refresh_token);
      
      // 메인 페이지로 리다이렉트
      window.location.href = '/chat';
      
    } catch (error) {
      console.error('로그인 실패:', error);
      alert('로그인에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    if (window.google) {
      window.google.accounts.id.prompt();
    } else {
      alert('Google 로그인을 사용할 수 없습니다. 잠시 후 다시 시도해주세요.');
    }
  };

  return (
    <LoginContainer>
      <Logo>오터스</Logo>
      <Subtitle>AI 개인 비서와 함께하세요</Subtitle>
      
      <GoogleButton onClick={handleGoogleLogin} disabled={isLoading}>
        <GoogleIcon />
        {isLoading ? '로그인 중...' : 'Google로 로그인'}
      </GoogleButton>
    </LoginContainer>
  );
};

export default LoginPage;
