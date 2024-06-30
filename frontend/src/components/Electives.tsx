import React from 'react';
import { BACKEND_URL } from './url';
import { toast, Toaster } from 'react-hot-toast';

const Electives: React.FC = () => {
    const getBreadth = async (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
        event.preventDefault();
        try {
            const response = await fetch(`${BACKEND_URL}/elective/breadth`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const blob = await response.blob(); // converts to binary large object
            const url = window.URL.createObjectURL(blob); // window.URL.createObjectURL(blob) creates a temporary URL that references the Blob object
            const a = document.createElement('a'); 
            a.href = url;   // link pointing to blob
            a.download = 'breadth_electives.csv'; // download on clicking link
            document.body.appendChild(a);
            a.click();
            toast.success("Successfully saved available breadth electives as breadth_electives.csv!");
            a.remove();
        } catch (error) {
            console.error('Error fetching breadth electives:', error);
            toast.error("Error fetching breadth electives!");
        }
    }

    const getDepth = async (event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
        event.preventDefault();
        try {
            const response = await fetch(`${BACKEND_URL}/elective/depth`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'depth_electives.csv';
            document.body.appendChild(a);
            a.click();
            toast.success("Successfully saved available depth electives as depth_electives.csv!");
            a.remove();
        } catch (error) {
            console.error('Error fetching depth electives:', error);
            toast.error("Error fetching depth electives!");
        }
    };

    return (
        <div>
            <Toaster position="bottom-center" />
            <div><h2>Choose depth/breadth electives</h2></div>
            <div className='electives'>
                <div><button className='download breadth' onClick={getBreadth}>Download breadth electives</button></div>
                <div><button className='download depth' onClick={getDepth}>Download depth electives</button></div>
            </div>
        </div>
    );
}

export default Electives;