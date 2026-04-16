import { Card, CardContent, Typography } from "@mui/material";
import { DataGrid } from '@mui/x-data-grid'

function EarningsTable( {earnings }) {
    
        const columns = [
            {field: 'date', headerName: 'Date', width: 150},
            {field: 'eps_actual', headerName: "EPS Actual", width: 130},
            {field: 'eps_estimate', headerName: "EPS Estimate", width: 130},
            {field: 'surprise', headerName: 'Surprise %', width: 130}
        ]  
    return (
        <Card>
            <CardContent>
                <Typography>Earnings Table</Typography>

                <DataGrid rows={earnings} columns={columns} />
        
            </CardContent>

        </Card>
    )
}

export default EarningsTable