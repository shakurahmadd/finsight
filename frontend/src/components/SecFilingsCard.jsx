import { Card, CardContent, Typography, Box, Divider, Chip } from "@mui/material";

function SecFilings({ filings }) {
    return (
        <Box sx={{ mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>SEC Filings</Typography>
            <Card>
                <CardContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>

                        <Box>
                            <Typography variant="subtitle1" sx={{ mb: 1, color: '#58a6ff' }}>Management Discussion</Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
                                {filings.management_discussion?.slice(0, 300)}...
                            </Typography>
                        </Box>

                        <Divider />

                        <Box>
                            <Typography variant="subtitle1" sx={{ mb: 1, color: '#58a6ff' }}>Risk Factors</Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
                                {filings.risk_factors?.slice(0, 300)}...
                            </Typography>
                        </Box>

                        <Divider />

                        <Box>
                            <Typography variant="subtitle1" sx={{ mb: 1, color: '#58a6ff' }}>Latest 8-K</Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.7 }}>
                                {filings.eight_k?.slice(0, 300)}...
                            </Typography>
                        </Box>

                        {filings.insider_traders?.length > 0 && (
                            <>
                                <Divider />
                                <Box>
                                    <Typography variant="subtitle1" sx={{ mb: 2, color: '#58a6ff' }}>Insider Trades</Typography>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                                        {filings.insider_traders?.map((trade) => (
                                            <Box
                                                key={trade.Date}
                                                sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 1.5, backgroundColor: '#0d1117', borderRadius: 1 }}
                                            >
                                                <Typography variant="body2" color="text.secondary">{trade.Date}</Typography>
                                                <Typography variant="body2">{trade.Shares?.toLocaleString()} shares</Typography>
                                                <Typography variant="body2">${trade.Price}</Typography>
                                                <Chip
                                                    label={trade.TransactionType}
                                                    size="small"
                                                    color={trade.TransactionType === 'P' ? 'success' : 'error'}
                                                    sx={{ fontWeight: 600 }}
                                                />
                                            </Box>
                                        ))}
                                    </Box>
                                </Box>
                            </>
                        )}

                    </Box>
                </CardContent>
            </Card>
        </Box>
    )
}

export default SecFilings
