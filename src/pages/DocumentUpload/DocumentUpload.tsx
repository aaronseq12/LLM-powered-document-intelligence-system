import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone, FileWithPath } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Button,
    Typography,
    Paper,
    CircularProgress,
    LinearProgress,
} from '@mui/material';
import { UploadFile as UploadFileIcon } from '@mui/icons-material';
import axios from 'axios';
import toast from 'react-hot-toast';

// Define a type for the processing status message from the backend
interface ProcessingStatus {
    document_id: string;
    status: 'processing' | 'analyzing' | 'enhancing' | 'completed' | 'failed';
    progress: number;
}

const DocumentUpload = () => {
    const navigate = useNavigate();
    const [file, setFile] = useState<FileWithPath | null>(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isUploading, setIsUploading] = useState(false);
    const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);

    // This useEffect hook establishes a real WebSocket connection
    useEffect(() => {
        // Use your machine's local IP or 'localhost' if running locally
        const ws = new WebSocket(`ws://localhost:8000/ws/client123`);

        ws.onmessage = (event) => {
            const message: ProcessingStatus = JSON.parse(event.data);
            // Only update status for the currently uploaded file
            if (processingStatus && message.document_id === processingStatus.document_id) {
                setProcessingStatus(message);

                if (message.status === 'completed') {
                    toast.success(`Processing complete for ${file?.name}!`);
                    setTimeout(() => navigate(`/documents/${message.document_id}`), 1000);
                } else if (message.status === 'failed') {
                    toast.error(`Processing failed for ${file?.name}.`);
                }
            }
        };

        ws.onerror = () => {
            toast.error("WebSocket connection error.");
        };

        // Clean up the connection when the component unmounts
        return () => {
            ws.close();
        };
    }, [processingStatus, file, navigate]);


    const onDrop = useCallback((acceptedFiles: FileWithPath[]) => {
        if (acceptedFiles.length > 0) {
            setFile(acceptedFiles[0]);
            setProcessingStatus(null);
            setUploadProgress(0);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'application/pdf': ['.pdf'] },
        multiple: false,
    });

    const handleUpload = async () => {
        if (!file) return;

        setIsUploading(true);
        setUploadProgress(0);
        setProcessingStatus(null);

        const formData = new FormData();
        formData.append('file', file);

        // This is a mock token. In a real app, you'd get this after logging in.
        const mockToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MjU1NjM5NTMwMH0.s_v83n-Y6_x46p3fCdt3-M-Q-i5s_x7m_X-B_z_y_Y0";


        try {
            const response = await axios.post('/api/documents/upload', formData, {
                onUploadProgress: (progressEvent) => {
                    if (progressEvent.total) {
                        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        setUploadProgress(percentCompleted);
                    }
                },
                headers: {
                    'Content-Type': 'multipart/form-data',
                    'Authorization': `Bearer ${mockToken}` // Add the required token
                },
            });

            toast.success('File uploaded! Processing has started...');
            const { document_id } = response.data;
            // Set initial processing status to link WebSocket messages to this upload
            setProcessingStatus({ document_id, status: 'processing', progress: 0 });

        } catch (error) {
            toast.error('Failed to upload file. Is the server running?');
            console.error(error);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <Box>
            <Typography variant="h4" gutterBottom>
                Upload a Document
            </Typography>
            <Paper
                {...getRootProps()}
                sx={{
                    p: 4,
                    textAlign: 'center',
                    border: `2px dashed ${isDragActive ? 'primary.main' : 'grey.500'}`,
                    cursor: 'pointer',
                    mb: 3,
                }}
            >
                <input {...getInputProps()} />
                <UploadFileIcon sx={{ fontSize: 60, color: 'grey.500' }} />
                <Typography>
                    {isDragActive ? 'Drop the file here ...' : 'Drag & drop a PDF here, or click to select a file'}
                </Typography>
            </Paper>

            {file && (
                <Box sx={{ mb: 2 }}>
                    <Typography variant="h6">Selected File:</Typography>
                    <Typography>{file.name}</Typography>
                </Box>
            )}

            {(isUploading || uploadProgress > 0 && uploadProgress < 100) && (
                <Box sx={{ width: '100%', mb: 2 }}>
                    <Typography>Uploading: {uploadProgress}%</Typography>
                    <LinearProgress variant="determinate" value={uploadProgress} />
                </Box>
            )}

            {processingStatus && (
                <Box sx={{ mb: 2 }}>
                    <Typography variant="h6">Processing Status:</Typography>
                    <Typography>Status: {processingStatus.status} - {processingStatus.progress}%</Typography>
                    <LinearProgress variant="determinate" value={processingStatus.progress} />
                </Box>
            )}


            <Button
                variant="contained"
                onClick={handleUpload}
                disabled={!file || isUploading || (!!processingStatus && processingStatus.status !== 'completed' && processingStatus.status !== 'failed')}
                startIcon={isUploading ? <CircularProgress size={20} /> : null}
            >
                {isUploading ? 'Uploading...' : 'Upload and Process'}
            </Button>
        </Box>
    );
};

export default DocumentUpload;

