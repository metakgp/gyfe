import React from 'react';
import { useForm } from 'react-hook-form';
import * as yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';
import { useNavigate } from 'react-router-dom';

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

    const getOTP = (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
      event.preventDefault(); // To Prevent reload
      // const securityAnswer = getValues('securityAnswer'); //Send this to an API and fetch otp
      console.log("Get otp"); 
    }
    
    const navigate = useNavigate();
    
    const onSubmit = () => {
      const otp = getValues('otp'); //Send this otp to api
      console.log(otp);
      updateStatus(); //call this method only if response is OK from api
      navigate('/');
    }

    return (
        <form className='login-form' onSubmit={handleSubmit(onSubmit)}>
            <div className='question'>
              <label>Security question: </label>  
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


