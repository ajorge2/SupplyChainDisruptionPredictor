// RealTimeInsights.js
import React, { useEffect, useState } from 'react';
import './RealTimeInsights.css';
import io from 'socket.io-client';

function RealTimeInsights() {
    const [insights, setInsights] = useState([]);

    useEffect(() => {
        console.log('Connecting to WebSocket...');
        const ws = new WebSocket('ws://localhost:8000/ws/realtime');
        
        ws.onopen = () => {
            console.log('WebSocket Connected');
        };
        
        ws.onmessage = (event) => {
            console.log('Received data:', event.data);
            const data = JSON.parse(event.data);
            setInsights(prev => [data, ...prev].slice(0, 10));
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
        };

        ws.onclose = () => {
            console.log('WebSocket Closed');
        };

        return () => {
            console.log('Cleaning up WebSocket');
            ws.close();
        };
    }, []);

    useEffect(() => {
        const socket = io('http://localhost:8000');
        socket.on('news_data', (data) => {
            console.log('Received news data:', data);
            // ... rest of your code
        });
    }, []);

    // Add debug render
    console.log('Current insights:', insights);

    const formatInsight = (data) => {
        switch(data.source) {
            case 'weather':
                return `Weather: ${data.main.temp}°C in ${data.name}`;
            case 'reddit':
                return `Reddit: New post in r/${data.subreddit} - "${data.title}"`;
            case 'news':
                return `News: ${data.title}`;
            default:
                return JSON.stringify(data);
        }
    };

    return (
        <div className="real-time-insights">
            <h3>Real-Time Insights</h3>
            <div className="insights-container">
                {insights.length === 0 && <p>Waiting for data...</p>}
                {insights.map((insight, index) => (
                    <div key={index} className="insight-item">
                        {formatInsight(insight)}
                        <span className="timestamp">
                            {new Date(insight.timestamp).toLocaleTimeString()}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default RealTimeInsights;