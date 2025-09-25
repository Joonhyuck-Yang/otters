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
`;

const GoogleIcon = styled.div`
  width: 20px;
  height: 20px;
  margin-right: 12px;
  background: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyMCAyMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwLjAwMDEgNC4xNjY2N0MxMS44MzM0IDQuMTY2NjcgMTMuNDE2NyA0LjgzMzMzIDE0LjU4MzQgNS45MTY2N0wxNy4wODM0IDMuNDE2NjdDMTUuMjUwMSAxLjY2NjY3IDEyLjU4MzQgMC41IDkuOTk5OTkgMC41QzYuNDE2NjcgMC41IDMuMjUwMDEgMi41ODMzMyAxLjI1MDAxIDUuNzQ5OTlMNC4wODMzNCA4LjA4MzMzQzUuNDE2NjcgNi4wODMzMyA3LjU4MzM0IDQuMTY2NjcgMTAuMDAwMSA0LjE2NjY3WiIgZmlsbD0iI0VBMjMzNiIvPgo8cGF0aCBkPSJNMTkuMTY2NyAxMC4yNUMxOS4xNjY3IDkuNTgzMzMgMTkuMDgzNCA4LjkxNjY3IDE4LjkxNjcgOC4zMzMzM0gMTB2My41SDIuMDgzMzRDMS4wODMzNCA2LjA4MzMzIDAuNSAzLjA4MzMzIDAuNSAwLjVIMTAuMDAwMUMxNS41IDAuNSAyMC4wMDAxIDQuNzUgMjAuMDAwMSAxMC4yNVoiIGZpbGw9IiM0Mjg1RjQiLz4KPHBhdGggZD0iTTEwIDIwQzcuNTgzMzQgMjAgNS4yNTAwMSAxOS4wODMzMyAzLjQxNjY3IDE3LjQxNjY3TDAuNTgzMzM0IDE0LjkxNjY3QzIuNzUwMDEgMTcuNDE2NjcgNi4wODMzNCAxOSAxMCAxOVoiIGZpbGw9IiMxNEE4NTMiLz4KPHBhdGggZD0iTTEwIDIwQzEyLjkxNjcgMjAgMTUuNjY2NyAxOS4wODMzMyAxNy45MTY3IDE3LjQxNjY3TDE0LjU4MzQgMTQuOTE2NjdDMTMuNDE2NyAxNS45MTY2NyAxMS44MzM0IDE2LjUgMTAgMTYuNUM3LjU4MzM0IDE2LjUgNS4yNTAwMSAxNS40MTY2NyAzLjQxNjY3IDEzLjc1TDAuNTgzMzM0IDE2LjI1QzIuNzUwMDEgMTguNzUgNi4wODMzNCAyMCAxMCAyMFoiIGZpbGw9IiNGRkJDMDQiLz4KPC9zdmc+') no-repeat center;
  background-size: contain;
`;

const LoginPage = () => {
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // 이미 로그인된 사용자인지 확인
    const token = localStorage.getItem('access_token');
    if (token) {
      // 토큰이 유효한지 확인하고 메인 페이지로 리다이렉트
      window.location.href = '/chat';
    }
  }, []);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    
    try {
      // Google OAuth2 로그인 처리
      // 실제 구현에서는 Google OAuth2 라이브러리를 사용해야 합니다
      
      // 임시로 테스트용 토큰 사용 (실제로는 Google OAuth2 플로우 필요)
      const mockGoogleToken = "test_google_token";
      
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${apiUrl}/api/auth/google`, {
        access_token: mockGoogleToken
      });
      
      // 토큰 저장
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
      
      // 메인 페이지로 리다이렉트
      window.location.href = '/chat';
      
    } catch (error) {
      console.error('로그인 실패:', error);
      alert('로그인에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
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
