import React from 'react';
import { useNavigate } from 'react-router-dom'

const Login: React.FC = () => {

    const navigate = useNavigate();
    const loginERP = () => {
      navigate("/electives");
    }

    return (
        <div className='login-form'>
            <div className='question'>
              <label>Security question: </label>
              <input type="text" placeholder='Enter your answer' className='input-box box'></input>
            </div>
            <div><button className='otp'>Send OTP</button></div>
            <div>
                <input type='text' placeholder='Enter OTP sent to email' className='input-box box'></input>
            </div>
            <div><button className='login-btn' type='submit' onClick={loginERP}>Login</button></div>
        </div>
    );
}

export default Login;