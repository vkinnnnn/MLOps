import React, { useState, useRef, useEffect } from 'react';
import { Send, FileText, Bot, PanelRightClose, PanelRightOpen, Sparkles, MessageSquarePlus, Maximize2, Upload, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import apiService from '../services/api';
import { ChatMessage, DocumentFile } from '../types';

interface DocumentIntegratorProps {
    documents: DocumentFile[];
    activeDocId: string | null;
    setActiveDocId: (id: string) => void;
    onUploadRequest: () => void;
    onDocumentUpdate?: (id: string, payload: Partial<DocumentFile>) => void;
}

const DocumentIntegrator: React.FC<DocumentIntegratorProps> = ({ documents, activeDocId, setActiveDocId, onUploadRequest, onDocumentUpdate }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [selectionMenu, setSelectionMenu] = useState<{x: number, y: number, text: string} | null>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const documentRef = useRef<HTMLDivElement>(null);
  const activeDoc = documents.find(d => d.id === activeDocId);

  useEffect(() => {
    if (activeDoc && activeDoc.documentId && !activeDoc.extractedData && onDocumentUpdate) {
      apiService.getDocumentExtractedData(activeDoc.documentId)
        .then((data) => {
          const extractedPayload = data.extracted_data || data;
          onDocumentUpdate(activeDoc.id, {
            extractedData: extractedPayload,
            content: activeDoc.content || data.extracted_text || extractedPayload?.complete_text?.merged_text || ''
          });
        })
        .catch((err) => console.error('Failed to hydrate extracted data', err));
    }
  }, [activeDoc?.documentId, activeDoc?.id, activeDoc?.content, onDocumentUpdate]);

  useEffect(() => {
    if (activeDoc) {
        setMessages([{ 
            role: 'model', 
            text: `Hello! I have loaded "${activeDoc.name}". I am ready to analyze its specific clauses, risks, or data points.`, 
            timestamp: new Date() 
        }]);
    } else {
        setMessages([]);
    }
  }, [activeDoc?.id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (textOverride?: string) => {
    const textToSend = textOverride || input;
    if (!textToSend.trim() || isLoading || !activeDoc) return;

    const userMsg: ChatMessage = { role: 'user', text: textToSend, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    
    if (!textOverride) setInput('');
    setIsLoading(true);

    try {
        // Use backend API for document analysis
        if (!activeDoc.documentId) {
            throw new Error('Document ID is required for backend analysis');
        }

        const response = await apiService.sendChatMessage(
            textToSend,
            activeDoc.documentId,
            activeDoc.extractedData,
            true // use memory
        );

        setMessages(prev => [...prev, { 
            role: 'model', 
            text: response.response || "No response generated.", 
            timestamp: new Date() 
        }]);
    } catch (err: any) {
        console.error('Backend chat error:', err);
        setMessages(prev => [...prev, { 
            role: 'model', 
            text: `Error analyzing document: ${err.message || 'Backend service unavailable'}. Please ensure the backend is running.`, 
            timestamp: new Date() 
        }]);
    } finally {
        setIsLoading(false);
    }
  };

  const handleMouseUp = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
        setSelectionMenu(null);
        return;
    }
    const text = selection.toString();
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    if (documentRef.current) {
         const containerRect = documentRef.current.getBoundingClientRect();
         setSelectionMenu({
             x: (rect.left + rect.width / 2) - containerRect.left,
             y: rect.top - containerRect.top - 45,
             text: text
         });
    }
  };

  const handleAskAboutSelection = () => {
      if (selectionMenu) {
          if (!isPanelOpen) setIsPanelOpen(true);
          handleSend(`Analyze this specific section:\n"${selectionMenu.text}"`);
          setSelectionMenu(null);
          window.getSelection()?.removeAllRanges();
      }
  };

  if (documents.length === 0) {
      return (
          <div className="flex flex-col h-full items-center justify-center bg-background text-textMuted space-y-6">
              <div className="relative">
                  <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full"></div>
                  <div className="w-20 h-20 bg-surfaceHighlight border border-border rounded-2xl flex items-center justify-center relative z-10 shadow-xl">
                    <FileText className="w-10 h-10 text-textMuted" />
                  </div>
              </div>
              <h2 className="text-2xl font-bold text-text">No Documents Available</h2>
              <p className="max-w-md text-center text-sm leading-relaxed">Upload documents to unlock the Deep Analysis tools.</p>
              <button onClick={onUploadRequest} className="flex items-center gap-2 px-8 py-3 bg-primary text-white rounded-xl font-medium hover:bg-primary/90 transition-all shadow-lg shadow-primary/25">
                  <Upload className="w-4 h-4" /> Go to Upload
              </button>
          </div>
      );
  }

  return (
    <div className="flex flex-col h-full bg-background overflow-hidden">
        
        {/* Navigation Bar */}
        <div className="h-16 bg-surface/80 backdrop-blur-md border-b border-border flex items-center px-4 gap-3 overflow-x-auto no-scrollbar shrink-0 z-20">
            {documents.map((doc) => (
                <button 
                    key={doc.id}
                    onClick={() => setActiveDocId(doc.id)}
                    className={`
                        relative group flex items-center gap-3 px-4 py-2 rounded-xl text-sm whitespace-nowrap transition-all border
                        ${activeDocId === doc.id 
                            ? 'bg-primary/10 border-primary/30 text-primary shadow-sm' 
                            : 'bg-transparent border-transparent text-textMuted hover:bg-surfaceHighlight hover:text-text'}
                    `}
                >
                    <FileText className="w-4 h-4" />
                    <span className="font-medium truncate max-w-[150px]">{doc.name}</span>
                    {activeDocId === doc.id && (
                        <motion.div layoutId="activeDocIndicator" className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary mx-4 rounded-t-full" />
                    )}
                </button>
            ))}
        </div>

        <div className="flex-1 flex overflow-hidden relative">
            
            {/* Document Viewer (Paper Metaphor) */}
            <div 
                ref={documentRef}
                className="flex-1 bg-zinc-100/5 dark:bg-[#0c0c0e] border-r border-border p-8 overflow-y-auto relative scroll-smooth"
                onMouseUp={handleMouseUp}
            >
                 <div className="absolute top-6 right-8 flex gap-2 z-20">
                    <AnimatePresence>
                        {!isPanelOpen && (
                            <motion.button 
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.8 }}
                                onClick={() => setIsPanelOpen(true)}
                                className="p-2.5 bg-primary text-white rounded-lg shadow-xl hover:bg-primary/90 transition-all"
                            >
                                <PanelRightOpen className="w-4 h-4" />
                            </motion.button>
                        )}
                    </AnimatePresence>
                    {isPanelOpen && (
                        <button onClick={() => setIsPanelOpen(false)} className="p-2 bg-black/5 hover:bg-black/10 dark:bg-white/10 dark:hover:bg-white/20 rounded-lg text-text transition-colors backdrop-blur-md">
                            <Maximize2 className="w-4 h-4" />
                        </button>
                    )}
                 </div>

                 {/* Paper Sheet */}
                 <motion.div 
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                    className="max-w-[850px] mx-auto bg-white min-h-[1100px] shadow-[0_20px_50px_-12px_rgba(0,0,0,0.5)] p-14 text-zinc-900 font-serif relative"
                 >
                    {activeDoc ? (
                        <>
                            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 opacity-80"></div>
                            <div className="flex justify-between items-center mb-10 border-b border-zinc-200 pb-4">
                                <span className="text-xs font-bold tracking-widest text-zinc-400 uppercase">Confidential Document</span>
                                <span className="text-xs font-mono text-zinc-400">{activeDoc.id}</span>
                            </div>
                            <h1 className="text-3xl font-bold mb-8 text-zinc-900 leading-tight">{activeDoc.name.replace(/\.[^/.]+$/, "").replace(/_/g, " ")}</h1>
                            <p className="text-justify leading-loose text-zinc-800 whitespace-pre-wrap font-serif text-[15px]">
                                {activeDoc.content}
                            </p>
                        </>
                    ) : (
                        <div className="h-full flex items-center justify-center text-zinc-300 italic">Select a document to view contents</div>
                    )}
                 </motion.div>

                 {/* Context Menu */}
                 <AnimatePresence>
                    {selectionMenu && (
                        <motion.div 
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="absolute z-50 transform -translate-x-1/2"
                            style={{ left: selectionMenu.x, top: selectionMenu.y }}
                        >
                            <button 
                                onClick={handleAskAboutSelection}
                                className="bg-zinc-900 text-white shadow-2xl rounded-full px-5 py-2.5 flex items-center gap-2 hover:bg-black transition-all group ring-1 ring-white/10"
                            >
                                <Sparkles className="w-4 h-4 text-purple-400 group-hover:animate-pulse" />
                                <span className="text-sm font-medium">Ask Copilot</span>
                            </button>
                            <div className="w-3 h-3 bg-zinc-900 transform rotate-45 absolute left-1/2 -ml-1.5 -bottom-1"></div>
                        </motion.div>
                    )}
                 </AnimatePresence>
            </div>

            {/* Chat Panel */}
            <motion.div 
                initial={{ width: 450, opacity: 1 }}
                animate={{ width: isPanelOpen ? 450 : 0, opacity: isPanelOpen ? 1 : 0 }}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="bg-surface/95 backdrop-blur-md border-l border-border flex flex-col z-30 shadow-2xl"
            >
                <div className="min-w-[450px] flex flex-col h-full"> 
                    <div className="p-5 border-b border-border flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-lg shadow-primary/20">
                                <Bot className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-bold text-sm text-text">Loan Copilot</h3>
                                <div className="flex items-center gap-1.5 mt-0.5">
                                    <span className={`w-1.5 h-1.5 rounded-full ${activeDoc ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.6)]' : 'bg-red-500'}`}></span>
                                    <span className="text-[10px] text-textMuted font-mono uppercase tracking-wider">{activeDoc ? 'ONLINE' : 'OFFLINE'}</span>
                                </div>
                            </div>
                        </div>
                        <button onClick={() => setIsPanelOpen(false)} className="p-2 hover:bg-surfaceHighlight rounded-lg text-textMuted hover:text-text transition-colors">
                            <PanelRightClose className="w-4 h-4" />
                        </button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-5 space-y-6">
                        {messages.length === 0 && (
                             <div className="flex flex-col items-center justify-center h-full text-textMuted opacity-50 space-y-3">
                                 <Bot className="w-12 h-12 stroke-1" />
                                 <p className="text-sm text-center font-medium">Ready to analyze <br/> <span className="text-primary">{activeDoc?.name}</span></p>
                             </div>
                        )}
                        {messages.map((msg, i) => (
                            <motion.div 
                                key={i} 
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div className={`
                                    max-w-[85%] rounded-2xl p-4 text-sm leading-relaxed shadow-sm
                                    ${msg.role === 'user' 
                                        ? 'bg-primary text-white rounded-br-sm' 
                                        : 'bg-surfaceHighlight border border-border text-text rounded-bl-sm'}
                                `}>
                                    {msg.text}
                                </div>
                            </motion.div>
                        ))}
                        {isLoading && (
                            <div className="flex justify-start">
                                 <div className="bg-surfaceHighlight border border-border rounded-2xl px-4 py-3 rounded-bl-sm flex gap-1.5 items-center">
                                    <span className="w-1.5 h-1.5 bg-textMuted/50 rounded-full animate-bounce"></span>
                                    <span className="w-1.5 h-1.5 bg-textMuted/50 rounded-full animate-bounce delay-100"></span>
                                    <span className="w-1.5 h-1.5 bg-textMuted/50 rounded-full animate-bounce delay-200"></span>
                                 </div>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>

                    <div className="p-5 border-t border-border bg-surface/50">
                        <div className="relative group">
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                                disabled={!activeDoc}
                                placeholder={activeDoc ? "Ask about specific clauses..." : "Select a document first..."}
                                className="w-full bg-background border border-border rounded-xl pl-4 pr-12 py-3.5 text-sm focus:outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all placeholder:text-textMuted/50 text-text shadow-sm"
                            />
                            <button 
                                onClick={() => handleSend()}
                                disabled={!input.trim() || isLoading || !activeDoc}
                                className="absolute right-2 top-2 p-1.5 bg-primary rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-all shadow-md active:scale-95"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    </div>
  );
};

export default DocumentIntegrator;