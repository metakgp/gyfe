import React from 'react';
import { useForm } from 'react-hook-form';
import * as yup from "yup";
import { yupResolver } from "@hookform/resolvers/yup";

interface IFormInput {
  roll: string;
  passwd: string;
}

//validation
const schema = yup.object().shape({
  roll: yup.string().required("Roll number is required!").matches(/^\d{2}[A-Z]{2}\d{5}$/, "Please enter valid roll number!"),
  passwd: yup.string().required("Password is required!")
});

interface FormProps {
  onSubmit: () => void;
}


const RollForm: React.FC<FormProps> = ({onSubmit}) => {

    const {register, handleSubmit, formState: {errors}} = useForm<IFormInput> ({ resolver: yupResolver(schema)});

    const handleFormSubmit = (data: IFormInput) => {
      console.log(data); // Or send data to an API endpoint
      onSubmit();
    }

    return (
        <form onSubmit={handleSubmit(handleFormSubmit)} method='POST'>
            <div className='roll'>
              <label>Roll number: </label>
              <input type="text" placeholder='Roll number for ERP, e.g. 22AE10024' className='input-box' {...register("roll")}/>
              {errors.roll && <p style={{color: "red"}}>{errors.roll.message}</p>}
            </div>
            <div className='passwd'>
              <label>Password: </label>
              <input type="password" placeholder='Password for ERP login' className='input-box' {...register("passwd")}/>
              {errors.passwd && <p style={{color: "red"}}>{errors.passwd.message}</p>}
            </div>
            <div><button type="submit" className='btn'>Get security question</button></div>
        </form>
    );
}

export default RollForm;