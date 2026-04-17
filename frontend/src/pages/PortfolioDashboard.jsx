import { Button, Container, TextField, Typography, Box } from "@mui/material";
import axios from "axios";
import { useEffect, useState } from "react";

function PortfolioDashboard () {
    const [isLoading, setIsLoading] = useState(false)
    const [portfolios, setPortfolios] = useState(null)
    const [selectedPortfolio, setSelectedPortfolio] = useState(null)
    const [error, setError] = useState('')
    const [newPortfolioName, setNewPortfolioName] = useState('')
    const [holdings, setHoldings] = useState(null)
    const [ticker, setTicker] = useState('')
    const [shares, setShares] = useState('')




    const fetchPortfolios = async () => {
        const token = localStorage.getItem('token')
        try {  
        const portfolioResponse = await axios.get("http://localhost:8000/portfolio", {headers: {Authorization: `Bearer ${token}`}})
        setPortfolios(portfolioResponse.data)
        }
        catch (error) {
            console.error(error)
            setError(error.response.data.detail)
        } }
    

    useEffect( () => {
        fetchPortfolios()
    }, [])


    const handleCreatePortfolio = async () => {
        const token = localStorage.getItem('token')
        try{
            const createPortfolioResponse = await axios.post("http://localhost:8000/portfolio", {name: newPortfolioName},
             {headers: {Authorization: `Bearer ${token}`}})
            setNewPortfolioName('')
            fetchPortfolios()

        }
        catch (error) {
            console.error(error)
            setError(error.response.data.detail)
        }
    }

    const handleDeletePortfolio = async (portfolioId) => {
        const token = localStorage.getItem('token')
        try{
            const deletePortfolioResponse = await axios.delete(`http://localhost:8000/portfolio/${portfolioId}`, 
            {headers : {Authorization: `Bearer ${token}`}})

            fetchPortfolios()

        } catch (error) {
            console.log(error)
            setError(error.response.data.detail)
        }
    }

    const handleSelectPortfolio = (portfolioId) => {
        setSelectedPortfolio(portfolioId)
    
    }

        
    const fetchHoldings = async () => {
        const token = localStorage.getItem('token')
        try{
            const fetchHoldingResponse = await axios.get(`http://localhost:8000/holdings/${selectedPortfolio}`, 
        {headers : {Authorization: `Bearer ${token}`}})
        setHoldings(fetchHoldingResponse.data)


        } catch (error) {
            console.log(error)
            setError(error.response.data.detail)
        }

    }

    useEffect(() => {
        if (selectedPortfolio == null) return
        fetchHoldings()
    }, [selectedPortfolio])

    const handleAddHolding = async () => {
        const token = localStorage.getItem('token')
        try{
            const addHoldingResponse = await axios.post(`http://localhost:8000/holdings/${selectedPortfolio}`,
            {ticker : ticker, shares : shares}, 
            {headers : {Authorization: `Bearer ${token}`}})
            fetchHoldings()
            setTicker('')
            setShares('')

        } catch (error) {
            console.log(error)
            setError(error.response.data.detail)

        }
    }

    const handleDeleteHolding = async (holding_id) => {
        const token = localStorage.getItem('token')
        try {

            const deleteHoldingResponse = await axios.delete(`http://localhost:8000/holdings/${selectedPortfolio}/${holding_id}`, 
            {headers : {Authorization: `Bearer ${token}`}})
            fetchHoldings()

        } catch (error) {
            console.log(error)
            setError(error.response.data.detail)
        }
    }
        


    return (
        <Container>                                                                                                                                           
            {selectedPortfolio === null ? (
                <Box>  
                    <Typography>My Portfolios</Typography>  
                    <TextField
                        value={newPortfolioName}
                        label="Portfolio Name"
                        onChange={(e) => setNewPortfolioName(e.target.value)}/>
                    <Button onClick={handleCreatePortfolio}>Create Portfolio</Button>                                                                                                                                    
                    {portfolios && portfolios.map((portfolio) => (
                    <Box key={portfolio.id}>
                    <Typography>{portfolio.name}</Typography>
                    <Button onClick={() => handleSelectPortfolio(portfolio.id)}>View</Button>
                    <Button onClick={() => handleDeletePortfolio(portfolio.id)}>Delete</Button>
                </Box>
            ))}                                                                                                              
                </Box>
            ) : (                                                                                                                                             
                <Box>  
                    <Typography>My Holdings</Typography>                                                                                                                                
                    <Button onClick={() => setSelectedPortfolio(null)}>Back</Button>

                    {holdings && holdings.map((holding) => (
                        <Box key = {holding.id}>
                        <Typography>{holding.ticker}</Typography>
                        <Typography>{holding.shares}</Typography>
                        <Button onClick={() => handleDeleteHolding(holding.id)}>Delete</Button>
                        </Box>
                         
                    ))}

                    <TextField
                    value = {ticker}
                    label = "Ticker"
                    onChange={(e) => setTicker(e.target.value)}
                    />
                    <TextField
                    value = {shares}
                    label = "Shares"
                    onChange={(e) => setShares(e.target.value)}
                    />
                    <Button onClick={handleAddHolding}>Add Holding</Button>

                </Box>
            )}
        </Container>
    )

}

export default PortfolioDashboard