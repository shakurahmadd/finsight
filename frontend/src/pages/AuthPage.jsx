import { Container, TextField, Typography, Box, Button, Alert} from "@mui/material";
import axios from "axios";
import { useState } from "react";
import { useNavigate } from "react-router-dom";


function AuthPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isloading, setIsLoading] = useState(false)
    const [error, setError] = useState('')
    const [confirmPassword, setConfirmPassword] = useState('')
    const navigate = useNavigate()

    const handleSubmit = async () => {
        setIsLoading(true)
        try {

            if (!isLogin && password !== confirmPassword) {
                setError('Passwords do not match')
                setIsLoading(false)
                return 
            }


            const loginResponse = isLogin ? await axios.post('http://localhost:8000/login', {email : email, password : password}) : 
            await axios.post('http://localhost:8000/register', {email : email, password : password})


            if (isLogin) {
                localStorage.setItem('token', loginResponse.data.access_token)
                navigate('/')
            } else {
                setIsLogin(true)
                setPassword('')
                setConfirmPassword('')
            }

        
        } catch (error) {                                                                                                                                     
            console.error(error) 
            setError(error.response?.data?.detail || "Something went wrong")
         } finally {
            setIsLoading(false)
        }
    }


    return (
        <Container>
            <Box>
                <Typography>{isLogin ? "Login" : "Register"}</Typography>
                <TextField 
                value = {email}
                label = "Email"
                onChange={(e) => setEmail(e.target.value)} 
                />
            </Box>
            <Box>
                <TextField 
                type = "password"
                value = {password}
                label = "Password"
                onChange={(e) => setPassword(e.target.value)} />
            </Box>

            {!isLogin && (
                <Box>
                    <TextField
                        type = "password"
                        value={confirmPassword}
                        label="Confirm Password"
                        onChange={ (e) => setConfirmPassword(e.target.value)} 
                        />
                </Box>

            )}

            <Box>
                <Button onClick={handleSubmit}>
                {isLogin ? "Login" : "Sign Up"}
                </Button>
            </Box>
            <Box>
                {error && <Alert severity="error">{error}</Alert>}
                <Button onClick={() => {setIsLogin(!isLogin); setError(''); setEmail(''); setPassword(''); setConfirmPassword('')}}>
                    {isLogin ? "Dont't have an account? Register" : "Already have an account? Login"}
                </Button>
            </Box>
               
        </Container>
    )
}

export default AuthPage