import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Calendar, Save, ArrowLeft } from 'lucide-react';
import axios from 'axios';

const DiaryContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1a1a1a;
  color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
`;

const Header = styled.div`
  display: flex;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #333;
  background: #2a2a2a;
`;

const BackButton = styled.button`
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.3s ease;
  margin-right: 15px;

  &:hover {
    background: #444;
  }
`;

const HeaderTitle = styled.h1`
  font-size: 24px;
  font-weight: bold;
  color: #ffffff;
  margin: 0;
`;

const DiaryForm = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
`;

const DateInput = styled.div`
  margin-bottom: 30px;
`;

const DateLabel = styled.label`
  display: block;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 10px;
  color: #ffffff;
`;

const DateInputField = styled.input`
  width: 100%;
  padding: 15px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  color: #ffffff;
  font-size: 16px;
  outline: none;
  transition: border-color 0.3s ease;

  &:focus {
    border-color: #007bff;
  }
`;

const DiaryTextArea = styled.textarea`
  flex: 1;
  width: 100%;
  padding: 20px;
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 8px;
  color: #ffffff;
  font-size: 16px;
  line-height: 1.6;
  outline: none;
  resize: none;
  transition: border-color 0.3s ease;
  margin-bottom: 30px;

  &:focus {
    border-color: #007bff;
  }

  &::placeholder {
    color: #888;
  }
`;

const SaveButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 15px 30px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s ease;
  align-self: flex-end;

  &:hover {
    background: #0056b3;
  }

  &:disabled {
    background: #444;
    cursor: not-allowed;
  }
`;

const DiaryPage = () => {
  const [diary, setDiary] = useState('');
  const [date, setDate] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // 현재 날짜와 시간을 기본값으로 설정
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    setDate(`${year}-${month}-${day}T${hours}:${minutes}`);
  }, []);

  const handleSave = async () => {
    if (!diary.trim() || !date) return;

    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('access_token');
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      
      const response = await axios.post(`${apiUrl}/api/diary`, {
        diary: diary.trim(),
        date: new Date(date).toISOString()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // 성공 메시지 표시
      alert('일기가 저장되었습니다!');
      
      // 폼 초기화
      setDiary('');
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      const hours = String(now.getHours()).padStart(2, '0');
      const minutes = String(now.getMinutes()).padStart(2, '0');
      setDate(`${year}-${month}-${day}T${hours}:${minutes}`);
      
    } catch (error) {
      console.error('일기 저장 실패:', error);
      alert('일기 저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    window.history.back();
  };

  return (
    <DiaryContainer>
      <Header>
        <BackButton onClick={handleBack}>
          <ArrowLeft size={20} />
        </BackButton>
        <HeaderTitle>일기 작성</HeaderTitle>
      </Header>

      <DiaryForm>
        <DateInput>
          <DateLabel>
            <Calendar size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            날짜 및 시간
          </DateLabel>
          <DateInputField
            type="datetime-local"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </DateInput>

        <DiaryTextArea
          placeholder="오늘의 일기를 작성해보세요..."
          value={diary}
          onChange={(e) => setDiary(e.target.value)}
        />

        <SaveButton onClick={handleSave} disabled={!diary.trim() || !date || isLoading}>
          <Save size={16} style={{ marginRight: '8px' }} />
          {isLoading ? '저장 중...' : '저장하기'}
        </SaveButton>
      </DiaryForm>
    </DiaryContainer>
  );
};

export default DiaryPage;
