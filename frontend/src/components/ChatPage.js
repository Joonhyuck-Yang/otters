import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import { Mic, MicOff, Send, Plus } from 'lucide-react';
import axios from 'axios';

const ChatContainer = styled.div`
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

const Logo = styled.div`
  font-size: 24px;
  font-weight: bold;
  color: #ffffff;
`;

const ChatArea = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
`;

const WelcomeMessage = styled.h1`
  font-size: 48px;
  font-weight: 300;
  margin-bottom: 20px;
  text-align: center;
  color: #ffffff;
`;

const InputContainer = styled.div`
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 800px;
  background: #2a2a2a;
  border-radius: 25px;
  padding: 15px 20px;
  border: 1px solid #444;
  transition: border-color 0.3s ease;

  &:focus-within {
    border-color: #007bff;
  }
`;

const AttachmentButton = styled.button`
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.3s ease;

  &:hover {
    background: #444;
  }
`;

const ChatInput = styled.input`
  flex: 1;
  background: none;
  border: none;
  color: #ffffff;
  font-size: 16px;
  outline: none;
  padding: 0 15px;

  &::placeholder {
    color: #888;
  }
`;

const VoiceButton = styled.button`
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: all 0.3s ease;
  margin-right: 10px;

  &:hover {
    background: #444;
    color: #007bff;
  }

  &.recording {
    color: #ff4444;
    background: #444;
  }
`;

const SendButton = styled.button`
  background: #007bff;
  border: none;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  transition: background-color 0.3s ease;

  &:hover {
    background: #0056b3;
  }

  &:disabled {
    background: #444;
    cursor: not-allowed;
  }
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  max-width: 800px;
  width: 100%;
`;

const Message = styled.div`
  margin-bottom: 20px;
  padding: 15px 20px;
  border-radius: 20px;
  max-width: 70%;
  word-wrap: break-word;

  &.user {
    background: #007bff;
    color: white;
    margin-left: auto;
    text-align: right;
  }

  &.assistant {
    background: #2a2a2a;
    color: #ffffff;
    margin-right: auto;
  }
`;

const ChatPage = () => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // 새 세션 생성
    createNewSession();
  }, []);

  const createNewSession = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post('/api/chat/new-session', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSessionId(response.data.session_id);
    } catch (error) {
      console.error('세션 생성 실패:', error);
    }
  };

  const sendMessage = async () => {
    if (!message.trim() || isLoading) return;

    const userMessage = { role: 'user', message: message.trim() };
    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsLoading(true);

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.post('/api/chat', {
        message: message.trim(),
        session_id: sessionId
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const assistantMessage = { 
        role: 'assistant', 
        message: response.data.message 
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('메시지 전송 실패:', error);
      const errorMessage = { 
        role: 'assistant', 
        message: '죄송합니다. 메시지를 전송할 수 없습니다.' 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // 음성 녹음 기능 구현 예정
  };

  return (
    <ChatContainer>
      <Header>
        <Logo>오터스 비서</Logo>
      </Header>

      {messages.length === 0 ? (
        <ChatArea>
          <WelcomeMessage>무엇이든 말씀만 주세요!</WelcomeMessage>
          <InputContainer>
            <AttachmentButton>
              <Plus size={20} />
            </AttachmentButton>
            <ChatInput
              type="text"
              placeholder="무엇이든 물어보세요"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
            />
            <VoiceButton 
              onClick={toggleRecording}
              className={isRecording ? 'recording' : ''}
            >
              {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
            </VoiceButton>
            <SendButton 
              onClick={sendMessage}
              disabled={!message.trim() || isLoading}
            >
              <Send size={20} />
            </SendButton>
          </InputContainer>
        </ChatArea>
      ) : (
        <>
          <MessagesContainer>
            {messages.map((msg, index) => (
              <Message key={index} className={msg.role}>
                {msg.message}
              </Message>
            ))}
            {isLoading && (
              <Message className="assistant">
                답변을 생성하고 있습니다...
              </Message>
            )}
            <div ref={messagesEndRef} />
          </MessagesContainer>
          
          <div style={{ padding: '20px', display: 'flex', justifyContent: 'center' }}>
            <InputContainer style={{ maxWidth: '600px' }}>
              <AttachmentButton>
                <Plus size={20} />
              </AttachmentButton>
              <ChatInput
                type="text"
                placeholder="무엇이든 물어보세요"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <VoiceButton 
                onClick={toggleRecording}
                className={isRecording ? 'recording' : ''}
              >
                {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
              </VoiceButton>
              <SendButton 
                onClick={sendMessage}
                disabled={!message.trim() || isLoading}
              >
                <Send size={20} />
              </SendButton>
            </InputContainer>
          </div>
        </>
      )}
    </ChatContainer>
  );
};

export default ChatPage;
