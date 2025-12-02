
import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, CheckCircle2, Loader2, X, Trash2, File, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { DocumentFile } from '../types';
import apiService from '../services/api';

interface UploadDocumentsProps {
    documents: DocumentFile[];
    setDocuments: React.Dispatch<React.SetStateAction<DocumentFile[]>>;
    onUpload: (files: DocumentFile[]) => void;
}

const UploadDocuments: React.FC<UploadDocumentsProps> = ({ documents, setDocuments, onUpload }) => {
  const [dragActive, setDragActive] = useState(false);
  const divRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [opacity, setOpacity] = useState(0);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!divRef.current) return;
    const div = divRef.current;
    const rect = div.getBoundingClientRect();
    setPosition({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        processFiles(Array.from(e.dataTransfer.files));
    }
  };

  const processFiles = async (uploadedFiles: File[]) => {
    // Create initial document entries
    const newDocs: DocumentFile[] = uploadedFiles.map(file => ({
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: `${(file.size / 1024 / 1024).toFixed(2)} MB`,
        type: file.type,
        status: 'uploading',
        uploadDate: new Date().toLocaleDateString(),
        content: '', 
        accuracy: 0
    }));

    onUpload(newDocs);

    // Upload files to backend API
    for (const doc of newDocs) {
        const file = uploadedFiles.find(f => f.name === doc.name);
        if (!file) continue;

        try {
            // Update status to processing
            setDocuments(prev => prev.map(f => f.id === doc.id ? {...f, status: 'processing'} : f));

            // Upload and extract document
            const response = await apiService.extractDocument(file);
            
            // Fetch full document content from backend
            let documentContent = '';
            let extractedData = response.extracted_data;
            
            try {
                // Try to get full document text content
                documentContent = await apiService.getDocumentContent(response.document_id);
                // Also try to get extracted data if available
                try {
                    const extracted = await apiService.getDocumentExtractedData(response.document_id);
                    extractedData = extracted;
                } catch (e) {
                    // Use extracted_data from response if available
                    extractedData = response.extracted_data;
                }
            } catch (e) {
                // Fallback to response data
                documentContent = JSON.stringify(response.extracted_data, null, 2);
                extractedData = response.extracted_data;
            }
            
            // Update with real data from backend
            setDocuments(prev => prev.map(f => 
                f.id === doc.id 
                    ? {
                        ...f, 
                        status: 'ready', 
                        accuracy: response.accuracy_metrics?.overall_accuracy || 0,
                        content: documentContent || JSON.stringify(extractedData, null, 2),
                        documentId: response.document_id,
                        extractedData: extractedData
                    } 
                    : f
            ));
        } catch (error) {
            console.error(`Failed to upload ${file.name}:`, error);
            setDocuments(prev => prev.map(f => 
                f.id === doc.id 
                    ? {...f, status: 'error'} 
                    : f
            ));
        }
    }
  };

  const handleRemoveFile = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDocuments(prev => prev.filter(f => f.id !== id));
  };

  const getStatusColor = (status: string) => {
      switch(status) {
          case 'ready': return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
          case 'processing': return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
          case 'error': return 'text-red-400 bg-red-400/10 border-red-400/20';
          default: return 'text-zinc-500 bg-zinc-500/10';
      }
  };

  return (
    <div className="h-full bg-background p-8 overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-10">
        
        {/* Header */}
        <div className="space-y-2">
            <h1 className="text-3xl font-bold text-text tracking-tight">Upload Documents</h1>
            <p className="text-textMuted max-w-2xl text-sm leading-relaxed">
                Ingest loan documents (PDF, Images) to initialize the extraction pipeline. 
                These files serve as the context layer for the <span className="text-primary">Voice Agent</span> and <span className="text-accent">CoPilot</span>.
            </p>
        </div>

        {/* Spotlight Drag Drop Zone */}
        <div 
            ref={divRef}
            onMouseMove={handleMouseMove}
            onMouseEnter={() => setOpacity(1)}
            onMouseLeave={() => setOpacity(0)}
            className={`
                relative h-32 rounded-xl flex flex-col items-center justify-center transition-all duration-300 cursor-pointer overflow-hidden group
                ${dragActive ? 'bg-primary/5 scale-[1.01]' : 'bg-surface/50 hover:bg-surface'}
            `}
            style={{
                boxShadow: '0 0 0 1px var(--color-border)',
            }}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-upload')?.click()}
        >
             {/* Spotlight Gradient */}
             <div
                className="pointer-events-none absolute -inset-px opacity-0 transition duration-300 group-hover:opacity-100"
                style={{
                    background: `radial-gradient(600px circle at ${position.x}px ${position.y}px, rgba(59, 130, 246, 0.15), transparent 40%)`,
                }}
             />

             <input 
                id="file-upload"
                type="file" 
                multiple
                className="hidden" 
                onChange={(e) => {
                    if (e.target.files) {
                        processFiles(Array.from(e.target.files));
                    }
                }}
             />
             <div className="flex flex-col items-center gap-3 z-10">
                <div className={`
                    w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500
                    ${dragActive ? 'bg-primary text-white shadow-lg shadow-primary/40' : 'bg-surfaceHighlight text-textMuted group-hover:text-primary group-hover:scale-110'}
                `}>
                    <Upload className="w-5 h-5" />
                </div>
                <div className="text-center space-y-1">
                    <h3 className="text-sm font-semibold text-text">Click or drag files to upload</h3>
                    <p className="text-xs text-textMuted font-mono">PDF, PNG, JPG (Max 50MB)</p>
                </div>
             </div>
        </div>

        {/* Uploaded Context Section */}
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold flex items-center gap-2 text-text">
                    Uploaded Context <span className="text-xs font-normal text-textMuted ml-2 bg-surfaceHighlight px-2 py-0.5 rounded-full">{documents.length}</span>
                </h2>
                {documents.length > 0 && (
                    <button 
                        onClick={() => setDocuments([])}
                        className="text-xs font-medium text-textMuted hover:text-red-400 flex items-center gap-1.5 transition-colors px-3 py-1.5 rounded-md hover:bg-red-400/10"
                    >
                        <Trash2 className="w-3.5 h-3.5" /> Clear All
                    </button>
                )}
            </div>

            {/* Table Format List */}
            <div className="border border-border rounded-xl bg-surface/30 backdrop-blur-sm overflow-hidden min-h-[300px] flex flex-col relative">
                
                {documents.length === 0 ? (
                    /* Empty State */
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-textMuted/40 space-y-3">
                         <div className="w-16 h-16 rounded-2xl border-2 border-dashed border-border flex items-center justify-center">
                             <File className="w-8 h-8 opacity-50" />
                         </div>
                        <p className="text-sm font-medium">No context loaded</p>
                    </div>
                ) : (
                    <div className="w-full">
                        {/* Table Header */}
                        <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-border bg-surfaceHighlight/30 text-[11px] font-bold text-textMuted uppercase tracking-wider">
                            <div className="col-span-5">File Name</div>
                            <div className="col-span-2">Size</div>
                            <div className="col-span-2">Date</div>
                            <div className="col-span-2">Status</div>
                            <div className="col-span-1 text-right"></div>
                        </div>
                        
                        {/* Table Rows */}
                        <div className="divide-y divide-border/50">
                            <AnimatePresence mode="popLayout">
                                {documents.map((file, i) => (
                                    <motion.div 
                                        key={file.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ delay: i * 0.05 }}
                                        className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-white/[0.02] transition-colors text-sm group"
                                    >
                                        {/* Name */}
                                        <div className="col-span-5 flex items-center gap-4 overflow-hidden">
                                            <div className="w-10 h-10 rounded-lg bg-surfaceHighlight border border-border flex items-center justify-center shrink-0">
                                                <FileText className="w-5 h-5 text-primary" strokeWidth={1.5} />
                                            </div>
                                            <div className="flex flex-col min-w-0">
                                                <span className="truncate font-medium text-text group-hover:text-primary transition-colors">{file.name}</span>
                                                <span className="text-[10px] text-textMuted md:hidden">{file.size}</span>
                                            </div>
                                        </div>

                                        {/* Size */}
                                        <div className="col-span-2 text-textMuted text-xs font-mono hidden md:block">{file.size}</div>

                                        {/* Date */}
                                        <div className="col-span-2 text-textMuted text-xs hidden md:block">{file.uploadDate}</div>

                                        {/* Status */}
                                        <div className="col-span-3 md:col-span-2">
                                             <span className={`text-[10px] px-2.5 py-1 rounded-full border inline-flex items-center gap-1.5 font-medium shadow-sm ${getStatusColor(file.status)}`}>
                                                {file.status === 'processing' && <Loader2 className="w-3 h-3 animate-spin" />}
                                                {file.status === 'ready' && <CheckCircle2 className="w-3 h-3" />}
                                                {file.status === 'error' && <AlertCircle className="w-3 h-3" />}
                                                {file.status.toUpperCase()}
                                            </span>
                                        </div>

                                        {/* Actions */}
                                        <div className="col-span-2 md:col-span-1 flex justify-end">
                                            <button 
                                                onClick={(e) => handleRemoveFile(e, file.id)}
                                                className="p-2 rounded-lg text-textMuted hover:text-red-400 hover:bg-red-400/10 transition-all opacity-0 group-hover:opacity-100"
                                                title="Remove file"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                        </div>
                    </div>
                )}
            </div>
        </div>

      </div>
    </div>
  );
};

export default UploadDocuments;
