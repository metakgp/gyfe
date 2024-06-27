import React from 'react';
import { useForm } from 'react-hook-form';
import * as yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';
import { useNavigate } from 'react-router-dom';
import { BACKEND_URL } from './url';

const schema = yup.object().shape({
  securityAnswer: yup.string().required('Security answer is required'),
  otp: yup.string().required('OTP is required').matches(/^\d{6}$/, 'Please enter valid 6-digit OTP!'),
});

interface IFormInput {
  securityAnswer: string;
  otp: string;
}

interface SecurityQueFormProps {
  updateStatus: () => void;
}

const SecurityQueForm: React.FC<SecurityQueFormProps> = ({updateStatus}) => {
  
    const {register, handleSubmit, getValues, formState: {errors},} = useForm<IFormInput>({resolver: yupResolver(schema)});

    const getOTP = async (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
      console.log("this called")
      event.preventDefault(); // To Prevent reload
      const security_answer = getValues('securityAnswer'); 
      const passwd = sessionStorage.getItem("passwd"); // hadnle the hashed password

      const formData = {
        secret_answer: security_answer,
        password: passwd,
      }

      try {
        const response = await fetch(`${BACKEND_URL}/request-otp`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(formData),
        });
    
        if (!response.ok) {
          throw new Error(`Error: ${response.statusText}`);
        }

        const responseData = await response.json();
        console.log(responseData.message); // Or can show this message using react-hot-toast
    
      } catch (error) {
        console.error("Error fetching OTP:", error); // To show error page
      }
    }
    
    const navigate = useNavigate();
    
    const onSubmit = async () => {
      const otp1 = getValues('otp'); 
      const otp_data = {
        otp: otp1,
      }
      try {
        const response = await fetch(`${BACKEND_URL}/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(otp_data),  // In api, this endpoint requests password and secret answer again. But I have given only otp. Can be changed later
        });
    
        if (!response.ok) {
          throw new Error(`Error: ${response.statusText}`);
        }

        const responseData = await response.json();
        console.log(responseData.message); // Or can show this message using react-hot-toast

        updateStatus(); 
        navigate('/');
    
      } 
      catch (error) {
        console.error("Error fetching OTP:", error); // To show error page
      }
    }

    return (
        <form className='login-form' onSubmit={handleSubmit(onSubmit)}>
            <div className='question'>
              <label>{sessionStorage.getItem("secret_question")}: </label>  
              <input type="text" placeholder='Enter your answer' className='input-box box' {...register('securityAnswer')}></input>
              {errors.securityAnswer && (<p style={{ color: 'red' }}>{errors.securityAnswer.message}</p>)}
            </div>
            <div><button className='otp' onClick={getOTP}>Send OTP</button></div>
            <div>
                <input type='text' placeholder='Enter OTP sent to email' className='input-box box' {...register('otp')}></input>
                {errors.otp && <p style={{ color: 'red' }}>{errors.otp.message}</p>}
            </div>
            <div><button className='login-btn' type='submit'>Login</button></div>
        </form>
    );
}

export default SecurityQueForm;


