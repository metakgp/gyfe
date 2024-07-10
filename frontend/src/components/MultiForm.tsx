import React, { useState } from 'react';
import RollForm from './RollForm';
import SecurityQueForm from './SecurityQueForm';


const MultiForm: React.FC = () => {
    const [showSecurityQueForm, setSecurityQueForm] = useState(false);

    const handleGetSecurityQuestion = () => {
        setSecurityQueForm(true);
    };

    return (
        <div>
          {!showSecurityQueForm && <RollForm onSubmit={handleGetSecurityQuestion} />}
          {showSecurityQueForm && <SecurityQueForm/>}
       </div>
    );
}

export default MultiForm;