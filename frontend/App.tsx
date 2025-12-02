
import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import TalkToDocuments from './components/TalkToDocuments';
import UploadDocuments from './components/UploadDocuments';
import DocumentIntegrator from './components/DocumentIntegrator';
import { ViewMode, DocumentFile } from './types';
import { motion, AnimatePresence } from 'framer-motion';
import apiService from './services/api';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>(ViewMode.UPLOAD);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  // Global Document State
  const [documents, setDocuments] = useState<DocumentFile[]>([]);
  const [activeDocId, setActiveDocId] = useState<string | null>(null);

  useEffect(() => {
    // Sync React state with localStorage/DOM on mount
    const savedTheme = localStorage.getItem('theme') as 'dark' | 'light' | null;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.setAttribute('data-theme', savedTheme);
    }
  }, []);

  const mapStatus = (status?: string): DocumentFile['status'] => {
    if (!status) return 'processing';
    if (status === 'completed' || status === 'ready') return 'ready';
    if (status === 'failed') return 'error';
    if (status === 'pending') return 'processing';
    return 'processing';
  };

  useEffect(() => {
    const loadDocumentsFromServer = async () => {
      try {
        const serverDocs = await apiService.listDocuments();
        if (!serverDocs || serverDocs.length === 0) {
          return;
        }
        const normalizedDocs: DocumentFile[] = serverDocs.map((doc) => ({
          id: doc.document_id,
          name: doc.file_name || doc.document_id,
          type: doc.file_type || 'application/pdf',
          size: doc.file_size_bytes ? `${(doc.file_size_bytes / 1024 / 1024).toFixed(2)} MB` : 'Unknown',
          status: mapStatus(doc.processing_status),
          uploadDate: doc.upload_timestamp
            ? new Date(doc.upload_timestamp).toLocaleDateString()
            : new Date().toLocaleDateString(),
          content: doc.extracted_text || doc.extracted_data?.complete_text?.merged_text || '',
          accuracy:
            doc.accuracy ??
            doc.accuracy_metrics?.overall_accuracy ??
            doc.extracted_data?.accuracy_metrics?.overall_accuracy ??
            0,
          documentId: doc.document_id,
          extractedData: doc.extracted_data,
        }));
        setDocuments((prev) => {
          if (prev.length > 0) {
            // Merge by documentId to avoid overwriting new uploads
            const existingIds = new Set(prev.map((doc) => doc.id));
            const merged = [...prev];
            normalizedDocs.forEach((doc) => {
              if (!existingIds.has(doc.id)) {
                merged.push(doc);
              }
            });
            return merged;
          }
          return normalizedDocs;
        });
      } catch (error) {
        console.error('Failed to load documents from backend', error);
      }
    };

    loadDocumentsFromServer();
  }, []);

  // Enforce Workflow: If no documents, force view to UPLOAD
  useEffect(() => {
    if (documents.length === 0 && currentView !== ViewMode.UPLOAD) {
      setCurrentView(ViewMode.UPLOAD);
    }
  }, [documents, currentView]);

  // Safety Check: Ensure activeDocId points to a valid document
  useEffect(() => {
    if (documents.length > 0) {
      if (!activeDocId || !documents.find(d => d.id === activeDocId)) {
        setActiveDocId(documents[0].id);
      }
    } else {
      setActiveDocId(null);
    }
  }, [documents, activeDocId]);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const handleUploadFiles = (newFiles: DocumentFile[]) => {
    setDocuments(prev => {
        const updated = [...newFiles, ...prev];
        if (!activeDocId && newFiles.length > 0) {
            setActiveDocId(newFiles[0].id);
        }
        return updated;
    });
    if (!activeDocId && newFiles.length > 0) {
        setActiveDocId(newFiles[0].id);
    }
  };

  const updateDocument = useCallback(
    (docId: string, payload: Partial<DocumentFile>) => {
      setDocuments((prev) =>
        prev.map((doc) => (doc.id === docId ? { ...doc, ...payload } : doc))
      );
    },
    [setDocuments]
  );


  const renderView = () => {
    switch (currentView) {
      case ViewMode.TALK_TO_DOCS:
        return (
            <TalkToDocuments 
                documents={documents}
                activeDocId={activeDocId}
                setActiveDocId={setActiveDocId}
                onDocumentUpdate={updateDocument}
                onUploadRequest={() => setCurrentView(ViewMode.UPLOAD)}
            />
        );
      case ViewMode.UPLOAD:
        return (
            <UploadDocuments 
                documents={documents} 
                setDocuments={setDocuments} 
                onUpload={handleUploadFiles}
            />
        );
      case ViewMode.COPILOT:
        return (
            <DocumentIntegrator 
                documents={documents}
                activeDocId={activeDocId}
                setActiveDocId={setActiveDocId}
                onDocumentUpdate={updateDocument}
                onUploadRequest={() => setCurrentView(ViewMode.UPLOAD)}
            />
        );
      default:
        return <UploadDocuments documents={documents} setDocuments={setDocuments} onUpload={handleUploadFiles} />;
    }
  };

  return (
    <div className="flex h-screen w-screen bg-background text-text overflow-hidden font-sans transition-colors duration-500 relative selection:bg-primary/20">
      
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.03] dark:opacity-[0.05]"
           style={{
             backgroundImage: `linear-gradient(to right, var(--color-border) 1px, transparent 1px),
                               linear-gradient(to bottom, var(--color-border) 1px, transparent 1px)`,
             backgroundSize: '40px 40px'
           }}
      />

      <Sidebar 
        currentView={currentView} 
        onViewChange={setCurrentView} 
        isOpen={isSidebarOpen}
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        theme={theme}
        toggleTheme={toggleTheme}
        hasDocuments={documents.length > 0}
      />
      
      <main className="flex-1 relative flex flex-col min-w-0 z-10">
        {!import.meta.env.VITE_GEMINI_API_KEY && !import.meta.env.GEMINI_API_KEY && (
           <div className="absolute top-0 left-0 right-0 bg-red-500/10 backdrop-blur-md text-red-200 p-2 text-center text-xs z-50 border-b border-red-500/20 font-mono">
             [System Warning] GEMINI_API_KEY environment variable missing.
           </div>
        )}
        
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="flex-1 h-full w-full"
          >
            {renderView()}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
};

export default App;
