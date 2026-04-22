import { Container, TextField, Typography, Box, Button, Alert, Card, CardContent } from "@mui/material";
import axios from "axios";
import { useState } from "react";
import { useNavigate } from "react-router-dom";


function AuthPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isLoading, setIsLoading] = useState(false)
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

            const loginResponse = isLogin
                ? await axios.post(`${import.meta.env.VITE_API_URL}/api/login`, { email, password })
                : await axios.post(`${import.meta.env.VITE_API_URL}/api/register`, { email, password })

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
        <Container maxWidth="xs">
            <Box sx={{ mt: 12, mb: 4, textAlign: 'center' }}>
                <Typography variant="h4" sx={{ color: '#58a6ff', fontWeight: 700, mb: 1 }}>
                    FinSight
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Autonomous financial research
                </Typography>
            </Box>

            <Card>
                <CardContent sx={{ p: 4 }}>
                    <Typography variant="h6" sx={{ mb: 3 }}>
                        {isLogin ? "Sign in to your account" : "Create an account"}
                    </Typography>

                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <TextField
                            fullWidth
                            value={email}
                            label="Email"
                            onChange={(e) => setEmail(e.target.value)}
                        />
                        <TextField
                            fullWidth
                            type="password"
                            value={password}
                            label="Password"
                            onChange={(e) => setPassword(e.target.value)}
                        />
                        {!isLogin && (
                            <TextField
                                fullWidth
                                type="password"
                                value={confirmPassword}
                                label="Confirm Password"
                                onChange={(e) => setConfirmPassword(e.target.value)}
                            />
                        )}

                        {error && <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>}

                        <Button
                            fullWidth
                            variant="contained"
                            onClick={handleSubmit}
                            disabled={isLoading}
                            sx={{ mt: 1, py: 1 }}
                        >
                            {isLogin ? "Sign In" : "Create Account"}
                        </Button>
                    </Box>

                    <Box sx={{ mt: 3, textAlign: 'center' }}>
                        <Button
                            size="small"
                            onClick={() => { setIsLogin(!isLogin); setError(''); setEmail(''); setPassword(''); setConfirmPassword('') }}
                            sx={{ color: '#8b949e', '&:hover': { color: '#58a6ff' } }}
                        >
                            {isLogin ? "Don't have an account? Register" : "Already have an account? Sign in"}
                        </Button>
                    </Box>
                </CardContent>
            </Card>
        </Container>
    )
}

export default AuthPage
