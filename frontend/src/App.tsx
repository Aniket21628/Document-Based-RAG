import React, { useState, useRef, useEffect } from 'react';
import { Upload, Send, FileText, MessageCircle, AlertCircle, CheckCircle } from 'lucide-react';
import { v4 as uuidv4 } from 'uuid';
import { uploadDocument, queryDocuments, getStatus } from './services/api';
import type { Message, UploadedFile, QueryStatus } from './types/index';
import './App.css';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Poll for status updates
  useEffect(() => {
    const pollStatuses = async () => {
      const pendingFiles = uploadedFiles.filter(file => 
        file.status === 'uploading' || file.status === 'processing'
      );
      
      for (const file of pendingFiles) {
        try {
          const status = await getStatus(file.trace_id);
          if (status.status === 'completed') {
            setUploadedFiles(prev => 
              prev.map(f => 
                f.trace_id === file.trace_id 
                  ? { ...f, status: 'completed' }
                  : f
              )
            );
          } else if (status.status === 'error') {
            setUploadedFiles(prev => 
              prev.map(f => 
                f.trace_id === file.trace_id 
                  ? { ...f, status: 'error' }
                  : f
              )
            );
          }
        } catch (error) {
          console.error('Error polling status:', error);
        }
      }
    };

    const interval = setInterval(pollStatuses, 2000);
    return () => clearInterval(interval);
  }, [uploadedFiles]);

  const handleFileUpload = async (files: FileList | null) => {
    if (!files) return;

    for (const file of Array.from(files)) {
      const fileData: UploadedFile = {
        name: file.name,
        size: file.size,
        type: file.type,
        upload_time: new Date(),
        trace_id: '',
        status: 'uploading'
      };

      setUploadedFiles(prev => [...prev, fileData]);

      try {
        const response = await uploadDocument(file);
        setUploadedFiles(prev =>
          prev.map(f =>
            f.name === file.name && f.upload_time === fileData.upload_time
              ? { ...f, trace_id: response.trace_id, status: 'processing' }
              : f
          )
        );

        // Add system message
        const systemMessage: Message = {
          id: uuidv4(),
          type: 'assistant',
          content: `Document "${file.name}" uploaded successfully and is being processed...`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, systemMessage]);

      } catch (error) {
        console.error('Upload error:', error);
        setUploadedFiles(prev =>
          prev.map(f =>
            f.name === file.name && f.upload_time === fileData.upload_time
              ? { ...f, status: 'error' }
              : f
          )
        );
      }
    }
  };

  const handleQuery = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: uuidv4(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await queryDocuments(inputValue);
      
      // Poll for result
      const pollResult = async () => {
        try {
          const status: QueryStatus = await getStatus(response.trace_id);
          
          if (status.status === 'completed' && status.result) {
            const assistantMessage: Message = {
              id: uuidv4(),
              type: 'assistant',
              content: status.result.response,
              timestamp: new Date(),
              sources: status.result.sources
            };
            setMessages(prev => [...prev, assistantMessage]);
            setIsLoading(false);
          } else if (status.status === 'error') {
            const errorMessage: Message = {
              id: uuidv4(),
              type: 'assistant',
              content: `Error processing query: ${status.error}`,
              timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
            setIsLoading(false);
          } else {
            setTimeout(pollResult, 1000);
          }
        } catch (error) {
          console.error('Error polling query status:', error);
          setIsLoading(false);
        }
      };

      setTimeout(pollResult, 1000);

    } catch (error) {
      console.error('Query error:', error);
      const errorMessage: Message = {
        id: uuidv4(),
        type: 'assistant',
        content: 'Sorry, there was an error processing your query.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  };

  const getFileStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-800">Agentic RAG Chatbot</h1>
          <p className="text-sm text-gray-600 mt-1">Multi-format Document QA</p>
        </div>
        
        {/* File Upload */}
        <div className="p-4">
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600">
              Drop files here or click to browse
            </p>
            <p className="text-xs text-gray-500 mt-1">
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
        </div>

        {/* Uploaded Files */}
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Uploaded Documents</h3>
          <div className="space-y-2">
            {uploadedFiles.map((file, index) => (
              <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-700 truncate">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
                {getFileStatusIcon(file.status)}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center text-gray-500 mt-20">
              <MessageCircle className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="text-lg font-medium">Welcome to Agentic RAG Chatbot</p>
              <p className="text-sm mt-2">Upload documents and start asking questions!</p>
            </div>
          )}
          
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl p-4 rounded-lg ${
                message.type === 'user' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-white border border-gray-200'
              }`}>
                <p className="text-sm">{message.content}</p>
                
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs text-gray-500 mb-2">Sources:</p>
                    <div className="space-y-1">
                      {message.sources.map((source, index) => (
                        <div key={index} className="text-xs bg-gray-50 p-2 rounded">
                          <p className="font-medium">{source.file_name}</p>
                          <p className="text-gray-600 mt-1">{source.content_preview}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <p className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-sm text-gray-600">Processing your query...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200 p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="Ask a question about your documents..."
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              onClick={handleQuery}
              disabled={!inputValue.trim() || isLoading}
              className="bg-blue-500 text-white p-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;