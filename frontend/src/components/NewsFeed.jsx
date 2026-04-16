import { Card, CardContent, Typography, Chip } from "@mui/material";

function NewsFeed({ news }) {
    return (
        <div>
            <Typography variant="h6" sx={{ mb: 2}}>Latest News</Typography>
            {news.map((article) => (                
                <Card key={article.title}>
        
                    <CardContent>
                        <Typography>{article.title}</Typography>
                        <Chip 
                            label={article.sentiment_label} 
                            size="small"
                            color={
                                article.sentiment_label == 'Bullish' ? 'success' :
                                article.sentiment_label == 'Bearish' ? 'error' :
                                'default'
                            }
                            
                            />
                        <Typography variant="body2">
                            {article.sentiment_confidence ? `${(article.sentiment_confidence * 100).toFixed(1)}%` : ''}
                        </Typography>
                    </CardContent>
                </Card>

            ))}
        </div>
    )
}

export default NewsFeed