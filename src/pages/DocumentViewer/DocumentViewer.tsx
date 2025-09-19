import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
    Box,
    Typography,
    Paper,
    TextField,
    Button,
    CircularProgress,
    Grid,
    List,
    ListItem,
    ListItemText
} from '@mui/material';
import axios from 'axios';
import toast from 'react-hot-toast';

const DocumentViewer = () => {
    const { documentId } = useParams();
    const [documentData, setDocumentData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [question, setQuestion] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isAnswering, setIsAnswering] = useState(false);

    useEffect(() => {
        const fetchDocument = async () => {
            try {
                // In a real app, you'd fetch the document data from your backend
                // For now, we'll use mock data.
                const mockData = {
                    data: {
                        full_text: "This is the full text of the PDF...",
                        summary: "This is a summary of the document.",
                        key_points: ["Point 1", "Point 2", "Point 3"]
                    }
                };
                setDocumentData(mockData);
            } catch (error) {
                toast.error('Failed to load document data.');
            } finally {
                setIsLoading(false);
            }
        };
        fetchDocument();
    }, [documentId]);

    const handleAskQuestion = async () => {
        if (!question.trim()) return;
        setIsAnswering(true);

        const newHistory = [...chatHistory, { role: 'user', content: question }];
        setChatHistory(newHistory);

        try {
            // Mocking the API call to the backend
            const mockResponse = `This is the LLM's answer to your question: "${question}"`;

            setChatHistory([...newHistory, { role: 'assistant', content: mockResponse }]);
            setQuestion('');

        } catch (error) {
            toast.error('Failed to get an answer.');
            setChatHistory(newHistory); // Revert history on error
        } finally {
            setIsAnswering(false);
        }
    };

    if (isLoading) {
        return <CircularProgress />;
    }

    return (
        <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
                <Typography variant="h5" gutterBottom>
                    Document Content
                </Typography>
                <Paper sx={{ p: 2, height: '70vh', overflowY: 'auto' }}>
                    <Typography variant="h6">Summary</Typography>
                    <Typography paragraph>{documentData?.data?.summary}</Typography>
                    <Typography variant="h6">Key Points</Typography>
                    <List>
                        {documentData?.data?.key_points.map((point, index) => (
                            <ListItem key={index}><ListItemText primary={point} /></ListItem>
                        ))}
                    </List>
                </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
                <Typography variant="h5" gutterBottom>
                    Chat with Document
                </Typography>
                <Paper sx={{ p: 2, height: '70vh', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ flexGrow: 1, overflowY: 'auto', mb: 2 }}>
                        {chatHistory.map((entry, index) => (
                            <Box key={index} sx={{ mb: 1, textAlign: entry.role === 'user' ? 'right' : 'left' }}>
                                <Typography variant="caption" color="text.secondary">{entry.role}</Typography>
                                <Paper sx={{ p: 1, display: 'inline-block', bgcolor: entry.role === 'user' ? 'primary.light' : 'grey.200' }}>
                                    {entry.content}
                                </Paper>
                            </Box>
                        ))}
                    </Box>
                    <Box sx={{ display: 'flex' }}>
                        <TextField
                            fullWidth
                            variant="outlined"
                            label="Ask a question about the document"
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleAskQuestion()}
                        />
                        <Button
                            variant="contained"
                            onClick={handleAskQuestion}
                            disabled={isAnswering}
                            sx={{ ml: 1 }}
                        >
                            {isAnswering ? <CircularProgress size={24} /> : 'Ask'}
                        </Button>
                    </Box>
                </Paper>
            </Grid>
        </Grid>
    );
};

export default DocumentViewer;
