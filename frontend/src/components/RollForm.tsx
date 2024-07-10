import React, {useContext, useState} from 'react';
import { useForm } from 'react-hook-form';
import * as yup from "yup";
import { yupResolver } from "@hookform/resolvers/yup";
import { BACKEND_URL } from './url';
import { UserContext } from '../app-context/user-context';
import { toast, Toaster } from 'react-hot-toast';

interface IFormInput {
  roll_number: string;
  passwd: string;
}

//validation
const schema = yup.object().shape({
  roll_number: yup.string().required("Roll number is required!").matches(/^\d{2}[A-Z]{2}\d{5}$/, "Please enter valid roll number!"),
  passwd: yup.string().required("Password is required!")
});

interface FormProps {
  onSubmit: () => void;
}


const RollForm: React.FC<FormProps> = ({onSubmit}) => {

    const {register, handleSubmit, formState: {errors}} = useForm<IFormInput> ({ resolver: yupResolver(schema)});
    const { user, updateState } = useContext(UserContext);
    const [roll, setRoll] = useState(user?.roll || '');
    const [password, setPasswd] = useState(user?.password || '');
    const [securityQue, setSecurityQue] = useState(user?.securityQue || '');

    const handleFormSubmit = async (data: IFormInput) => {
      // sessionStorage.setItem("passwd",data.passwd); // Hash the password, then store. Stored for use in next form
      setRoll(data.roll_number);
      setPasswd(data.passwd);
      
      try {
        const formData = new URLSearchParams();
        formData.append("roll_number", data.roll_number);
        formData.append("password", data.passwd);

        const response = await fetch(`${BACKEND_URL}/secret-question`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData.toString(),
        })
    
        if (!response.ok) {
          throw new Error(`Error: ${response.statusText}`);
        }
    
        const responseData = await response.json(); // returns session token and secret question
        sessionStorage.setItem("SESSION_TOKEN",responseData.SESSION_TOKEN) //store session token
        toast.success("Fetched security question!");
        // sessionStorage.setItem("secret_question",responseData.secret_question) 
        setSecurityQue(responseData.SECRET_QUESTION);
        updateState({ user: { ...user, roll, password, securityQue} });
        onSubmit();
      } 
      catch (error) {
        console.error("Error fetching secret question:", error); // Here handle error. Can show that ErrorPage.tsx
        toast.error("Error fetching secret question!");
      }
      onSubmit();
    }

    return (
      <div className='roll-form'>
        <form onSubmit={handleSubmit(handleFormSubmit)}>
          <Toaster position="bottom-center" />
            <div className='roll'>
              <label>Roll number: </label>
              <input type="text" placeholder='Roll number for ERP' className='input-box' {...register("roll_number")}/>
              {errors.roll_number && <p style={{color: "red"}}>{errors.roll_number.message}</p>}
            </div>
            <div className='passwd'>
              <label>Password: </label>
              <input type="password" placeholder='Password for ERP login' className='input-box' {...register("passwd")}/>
              {errors.passwd && <p style={{color: "red"}}>{errors.passwd.message}</p>}
            </div>
            <div className='que-btn'><button type="submit" className='btn'>Get security question</button></div>
        </form>
      </div>
    );
}

export default RollForm;