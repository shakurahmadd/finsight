import { Card, CardContent, Typography } from "@mui/material";

function SecFilings( {filings} ) {
    return (
        <div>
            <Typography variant="h6" sx={{ mb: 2}}>SEC Filing Summary</Typography>

            <Card>
                <CardContent>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mt: 2 }}>Management Discussion</Typography>
                    <Typography variant="body2">{filings.management_discussion?.slice(0, 300)}...</Typography>                    


                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mt: 2 }}>Risk Factors</Typography>                                                              
                    <Typography variant="body2">{filings.risk_factors?.slice(0, 300)}...</Typography>  


                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mt: 2 }}>Latest 8-K</Typography>                                                                
                    <Typography variant="body2">{filings.eight_k?.slice(0, 300)}...</Typography> 

                    
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mt: 2 }}>Insider Trades</Typography>
                    {filings.insider_traders?.map((trade) => (
                        <div key={trade.Date}>
                            <Typography variant="body2">Date: {trade.Date}</Typography>                                                                                       
                            <Typography variant="body2">Shares: {trade.Shares}</Typography>                                                                                   
                            <Typography variant="body2">Price: ${trade.Price}</Typography>                                                                                    
                            <Typography variant="body2">Type: {trade.TransactionType}</Typography>   
                        </div>
                    ))}
                            
                </CardContent>
            </Card>
        </div>
    )
}

export default SecFilings