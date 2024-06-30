import React, { useState } from 'react';
import RollForm from './RollForm';
import SecurityQueForm from './SecurityQueForm';

interface MultiFormProps {
    updateStatus: () => void;
}

const MultiForm: React.FC<MultiFormProps> = ({updateStatus}) => {
    const [showSecurityQueForm, setSecurityQueForm] = useState(false);

    const handleGetSecurityQuestion = () => {
        setSecurityQueForm(true);
    };

    return (
        <div>
          {!showSecurityQueForm && <RollForm onSubmit={handleGetSecurityQuestion} />}
          {showSecurityQueForm && <SecurityQueForm updateStatus = {updateStatus}/>}
       </div>
    );
}

export default MultiForm;