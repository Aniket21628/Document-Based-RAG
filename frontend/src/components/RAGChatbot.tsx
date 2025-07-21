import React, { useState, useRef, useEffect } from 'react';
import type { KeyboardEvent } from 'react';
import {
  Upload,
  Send,
  MessageCircle,
  FileText,
  Trash2,
  Loader,
  CheckCircle,
  AlertCircle,
  Bot,
  User
} from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';

interface Message {
  type: 'user' | 'bot' | 'system' | 'error';
  content: string;
  timestamp: string;
  sources?: string[];
  confidence?: number;
}

const RAGChatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [sessionId] = useState<string>(() => `session-${Date.now()}`);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    setIsUploading(true);
    const formData = new FormData();
    Array.from(files).forEach(file => formData.append('files', file));

    try {
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setUploadedFiles(prev => [...prev, ...result.processed_files]);
        setMessages(prev => [
          ...prev,
          {
            type: 'system',
            content: `✅ Successfully processed ${result.processed_files.length} file(s): ${result.processed_files.map((f: string) => f.split('/').pop()).join(', ')}`,
            timestamp: new Date().toLocaleTimeString()
          }
        ]);
      } else {
        setMessages(prev => [
          ...prev,
          {
            type: 'error',
            content: `❌ Upload failed: ${result.error || 'Unknown error'}`,
            timestamp: new Date().toLocaleTimeString()
          }
        ]);
      }
    } catch (error: any) {
      setMessages(prev => [
        ...prev,
        {
          type: 'error',
          content: `❌ Upload error: ${error.message}`,
          timestamp: new Date().toLocaleTimeString()
        }
      ]);
    } finally {
      setIsUploading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    const newUserMessage: Message = {
      type: 'user',
      content: userMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, newUserMessage]);

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userMessage,
          session_id: sessionId
        }),
      });

      const result = await response.json();

      if (result.success) {
        const botMessage: Message = {
          type: 'bot',
          content: result.answer,
          sources: result.sources || [],
          confidence: result.confidence,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, botMessage]);
      } else {
        const errorMessage: Message = {
          type: 'error',
          content: `❌ Error: ${result.error || 'Failed to get response'}`,
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (error: any) {
      const errorMessage: Message = {
        type: 'error',
        content: `❌ Network error: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversation = async () => {
    try {
      await fetch(`${API_BASE_URL}/conversation/${sessionId}`, {
        method: 'DELETE'
      });
      setMessages([]);
    } catch (error) {
      console.error('Error clearing conversation:', error);
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <div className="bg-black/20 backdrop-blur-sm border-b border-purple-500/20">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-lg">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Agentic RAG Chatbot</h1>
                <p className="text-purple-200 text-sm">Multi-format Document QA with MCP</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-purple-200">
                {uploadedFiles.length} document(s) indexed
              </div>
              <button
                onClick={clearConversation}
                className="p-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-300 hover:text-red-200 transition-colors"
                title="Clear conversation"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Upload Panel */}
          <div className="lg:col-span-1">
            <div className="bg-black/40 backdrop-blur-sm rounded-xl p-6 border border-purple-500/20">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                <Upload className="w-5 h-5 mr-2 text-purple-400" />
                Upload Documents
              </h3>
              
              <div 
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-purple-500/30 rounded-lg p-8 text-center cursor-pointer hover:border-purple-500/50 hover:bg-purple-500/5 transition-all"
              >
                <Upload className="w-8 h-8 text-purple-400 mx-auto mb-3" />
                <p className="text-purple-200 text-sm mb-2">
                  Click to upload documents
                </p>
                <p className="text-purple-300 text-xs">
                  PDF, DOCX, PPTX, CSV, TXT, MD
                </p>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.docx,.pptx,.csv,.txt,.md"
                onChange={(e) => handleFileUpload(e.target.files)}
                className="hidden"
              />

              {isUploading && (
                <div className="mt-4 flex items-center justify-center space-x-2 text-purple-300">
                  <Loader className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Processing files...</span>
                </div>
              )}

              {uploadedFiles.length > 0 && (
                <div className="mt-6">
                  <h4 className="text-sm font-medium text-purple-300 mb-3">Indexed Files:</h4>
                  <div className="space-y-2">
                    {uploadedFiles.map((file, idx) => (
                      <div key={idx} className="flex items-center space-x-2 text-xs text-purple-200 bg-purple-500/10 rounded-lg p-2">
                        <FileText className="w-3 h-3 text-purple-400" />
                        <span className="truncate">{file.split('/').pop()}</span>
                        <CheckCircle className="w-3 h-3 text-green-400 flex-shrink-0" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chat Panel */}
          <div className="lg:col-span-3">
            <div className="bg-black/40 backdrop-blur-sm rounded-xl border border-purple-500/20 h-[600px] flex flex-col">
              {/* Chat Header */}
              <div className="p-4 border-b border-purple-500/20">
                <div className="flex items-center space-x-2">
                  <MessageCircle className="w-5 h-5 text-purple-400" />
                  <h3 className="text-lg font-semibold text-white">Chat Interface</h3>
                </div>
              </div>

              {/* Messages Area */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4">
                {messages.length === 0 && (
                  <div className="text-center text-purple-300 py-8">
                    <Bot className="w-12 h-12 mx-auto mb-4 text-purple-400" />
                    <p className="text-lg font-medium mb-2">Welcome to the RAG Chatbot!</p>
                    <p className="text-sm">Upload documents and start asking questions.</p>
                  </div>
                )}

                {messages.map((message, idx) => (
                  <div key={idx} className="animate-fade-in">
                    {message.type === 'user' && (
                      <div className="flex justify-end">
                        <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg px-4 py-3 max-w-[80%]">
                          <div className="flex items-center space-x-2 mb-1">
                            <User className="w-4 h-4" />
                            <span className="text-xs opacity-90">{message.timestamp}</span>
                          </div>
                          <p className="whitespace-pre-wrap">{message.content}</p>
                        </div>
                      </div>
                    )}

                    {message.type === 'bot' && (
                      <div className="flex justify-start">
                        <div className="bg-slate-800 text-white rounded-lg px-4 py-3 max-w-[80%] border border-purple-500/20">
                          <div className="flex items-center space-x-2 mb-2">
                            <Bot className="w-4 h-4 text-purple-400" />
                            <span className="text-xs text-purple-300">{message.timestamp}</span>
                            {message.confidence && (
                              <span className="text-xs text-green-400">
                                {Math.round(message.confidence * 100)}% confidence
                              </span>
                            )}
                          </div>
                          <p className="whitespace-pre-wrap mb-3">{message.content}</p>
                          {message.sources && message.sources.length > 0 && (
                            <div className="border-t border-purple-500/20 pt-3">
                              <p className="text-xs text-purple-300 mb-2">📚 Sources:</p>
                              <div className="space-y-1">
                                {message.sources.map((source, sourceIdx) => (
                                  <div key={sourceIdx} className="text-xs text-purple-200 bg-purple-500/10 rounded px-2 py-1">
                                    {source}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {(message.type === 'system' || message.type === 'error') && (
                      <div className="flex justify-center">
                        <div className={`${message.type === 'error' ? 'bg-red-500/20 text-red-300 border-red-500/20' : 'bg-blue-500/20 text-blue-300 border-blue-500/20'} rounded-lg px-4 py-2 text-sm border`}>
                          <div className="flex items-center space-x-2">
                            {message.type === 'error' ? (
                              <AlertCircle className="w-4 h-4" />
                            ) : (
                              <CheckCircle className="w-4 h-4" />
                            )}
                            <span>{message.content}</span>
                            <span className="text-xs opacity-75">{message.timestamp}</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800 text-white rounded-lg px-4 py-3 border border-purple-500/20">
                      <div className="flex items-center space-x-2">
                        <Bot className="w-4 h-4 text-purple-400" />
                        <Loader className="w-4 h-4 animate-spin text-purple-400" />
                        <span className="text-purple-300">Thinking...</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="p-4 border-t border-purple-500/20">
                <div className="flex space-x-3">
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask a question about your documents..."
                    className="flex-1 bg-slate-800 text-white border border-purple-500/30 rounded-lg px-4 py-3 resize-none focus:outline-none focus:border-purple-500 placeholder-purple-300"
                    rows={1}
                    style={{ minHeight: '44px', maxHeight: '120px' }}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isLoading}
                    className="px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-all"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
                <p className="text-xs text-purple-300 mt-2">
                  Press Enter to send, Shift+Enter for new line
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default RAGChatbot;