import React from 'react';

const Electives: React.FC = () => {
    return (
        <div>
            <div><h2>Choose depth/breadth electives</h2></div>
            <div className='electives'>
                <div><button className='download breadth'>Download breadth electives</button></div>
                <div><button className='download depth'>Download depth electives</button></div>
            </div>
        </div>
    );
}

export default Electives;