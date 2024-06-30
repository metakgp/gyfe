import React, {useContext} from 'react';
import { useForm } from 'react-hook-form';
import * as yup from 'yup';
import { yupResolver } from '@hookform/resolvers/yup';
import { useNavigate } from 'react-router-dom';
import { BACKEND_URL } from './url';
import { UserContext } from '../app-context/user-context';
import { toast, Toaster } from 'react-hot-toast';

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
    const { user, updateState } = useContext(UserContext);

    const getOTP = async (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
      event.preventDefault(); // To Prevent reload
      const securityAns = getValues('securityAnswer'); 
      // const passwd = sessionStorage.getItem("passwd"); // hadnle the hashed password
      const passwd = user?.password;
      updateState({ user: { ...user, securityAns} });

      // Test if global state works
      console.log(user?.roll)
      console.log(user?.password)
      console.log(user?.securityQue)
      console.log(user?.securityAns)

      const formData = {
        secret_answer: securityAns,
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
        console.log(responseData.message); 
        toast.success("OTP sent successfully to ERP registered email id!");
    
      } catch (error) {
        console.error("Error fetching OTP:", error); 
        toast.error("Error fetching OTP!");
      }
    }
    
    const navigate = useNavigate();
    
    const onSubmit = async () => {
      const otp1 = getValues('otp'); 
      const login_data = {
        passw: user?.password,
        secretAns: user?.securityAns,
        otp: otp1,
      }
      try {
        const response = await fetch(`${BACKEND_URL}/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(login_data),  
        });
    
        if (!response.ok) {
          throw new Error(`Error: ${response.statusText}`);
        }

        const responseData = await response.json();
        console.log(responseData.message); 
        toast.success("Successfully logged in to ERP!");

        updateStatus(); 
        navigate('/');
    
      } 
      catch (error) {
        console.error("User not logged in", error);
        toast.error("Error logging to ERP! Please try again and ensure to enter correct credentials");
        navigate('/login'); // redirecting back to /login
      }
    }

    return (
        <form className='login-form' onSubmit={handleSubmit(onSubmit)}>
           <Toaster position="bottom-center" />
            <div className='question'>
              <label>{user?.securityQue}: </label>  
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


