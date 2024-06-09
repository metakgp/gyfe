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

const Form: React.FC = () => {
    const {register, handleSubmit, formState: {errors}} = useForm<IFormInput> ({ resolver: yupResolver(schema)});
    const onSubmit = (data: IFormInput) => {
      console.log(data);
    }

    return (
        <form onSubmit={handleSubmit(onSubmit)} method='POST'>
            <div className='roll'>
              <label>Roll number: </label>
              <input type="text" placeholder='Roll number for ERP, e.g. 22AE10024' {...register("roll")}/>
              {errors.roll && <p>{errors.roll.message}</p>}
            </div>
            <div className='passwd'>
              <label>Password: </label>
              <input type="password" placeholder='Password for ERP login' {...register("passwd")}/>
              {errors.passwd && <p>{errors.passwd.message}</p>}
            </div>
            <div><input type="submit" className='btn' value="Get security question"/></div>
        </form>
    );
}

export default Form;