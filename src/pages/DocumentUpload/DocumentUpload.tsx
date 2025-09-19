import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Button,
    Typography,
    Paper,
    CircularProgress,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    LinearProgress,
} from '@mui/material';
import { UploadFile, CheckCircle, ErrorOutline } from '@mui/icons-material';
import axios from 'axios';
import toast from 'react-hot-toast';

// This is a mock WebSocket hook for demonstration purposes.
// In a real app, you would connect to your backend WebSocket.
const useMockSocket = (onMessage) => {
    // Simulates receiving messages from a WebSocket
    const simulateMessage = (documentId, status, progress) => {
        setTimeout(() => {
            onMessage({ data: JSON.stringify({ document_id: documentId, status, progress }) });
        }, progress * 50); // Simulate delay
    };

    return { simulateMessage };
};


const DocumentUpload = () => {
    const navigate = useNavigate();
    const [file, setFile] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isUploading, setIsUploading] = useState(false);
    const [processingStatus, setProcessingStatus] = useState(null);

    const onUploadProgress = (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(percentCompleted);
    };

    const handleProcessingMessage = (event) => {
        const message = JSON.parse(event.data);
        setProcessingStatus(message);

        if (message.status === 'completed') {
            toast.success(`Processing complete for ${file.name}!`);
            setTimeout(() => navigate(`/documents/${message.document_id}`), 1000);
        } else if (message.status === 'failed') {
            toast.error(`Processing failed for ${file.name}.`);
        }
    };

    // Replace with your actual WebSocket connection
    const { simulateMessage } = useMockSocket(handleProcessingMessage);


    const onDrop = useCallback((acceptedFiles) => {
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
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post('/api/documents/upload', formData, {
                onUploadProgress,
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            toast.success('File uploaded successfully! Starting processing...');
            const { document_id } = response.data;

            // Simulate WebSocket messages for processing status
            simulateMessage(document_id, 'processing', 10);
            simulateMessage(document_id, 'analyzing', 50);
            simulateMessage(document_id, 'enhancing', 90);
            simulateMessage(document_id, 'completed', 100);

        } catch (error) {
            toast.error('Failed to upload file.');
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
                <UploadFile sx={{ fontSize: 60, color: 'grey.500' }} />
                <Typography>
                    {isDragActive ? 'Drop the file here ...' : 'Drag & drop a PDF here, or click to select a file'}
                </Typography>
            </Paper>

            {file && !isUploading && (
                <Box sx={{ mb: 2 }}>
                    <Typography variant="h6">Selected File:</Typography>
                    <Typography>{file.name}</Typography>
                </Box>
            )}

            {isUploading && (
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
                disabled={!file || isUploading || (processingStatus && processingStatus.status !== 'completed')}
                startIcon={isUploading ? <CircularProgress size={20} /> : null}
            >
                {isUploading ? 'Uploading...' : 'Upload and Process'}
            </Button>
        </Box>
    );
};

export default DocumentUpload;
