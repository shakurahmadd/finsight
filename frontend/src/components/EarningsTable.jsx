import { Card, CardContent, Typography, Box } from "@mui/material";
import { DataGrid } from '@mui/x-data-grid'

function EarningsTable({ earnings }) {
    const columns = [
        { field: 'date', headerName: 'Date', flex: 1 },
        { field: 'eps_actual', headerName: 'EPS Actual', flex: 1, type: 'number' },
        { field: 'eps_estimate', headerName: 'EPS Estimate', flex: 1, type: 'number' },
        {
            field: 'surprise',
            headerName: 'Surprise %',
            flex: 1,
            type: 'number',
            renderCell: (params) => (
                <Typography
                    variant="body2"
                    sx={{ color: params.value > 0 ? '#3fb950' : params.value < 0 ? '#f85149' : '#e6edf3' }}
                >
                    {params.value > 0 ? '+' : ''}{params.value?.toFixed(1)}%
                </Typography>
            )
        }
    ]

    return (
        <Card sx={{ mb: 2 }}>
            <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>Earnings History</Typography>
                <Box sx={{ height: 300 }}>
                    <DataGrid
                        rows={earnings}
                        columns={columns}
                        pageSizeOptions={[5]}
                        initialState={{ pagination: { paginationModel: { pageSize: 5 } } }}
                        disableRowSelectionOnClick
                        sx={{ border: 'none' }}
                    />
                </Box>
            </CardContent>
        </Card>
    )
}

export default EarningsTable
