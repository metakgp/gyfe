import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import './styles/App.scss'
import Header from './components/Header'
import Footer from './components/Footer'
import Electives from './components/Electives';
import MultiForm from './components/MultiForm';
import ErrorPage from './components/ErrorPage';

const App: React.FC = () => {

  const [isLoggedIn, setLogin] = useState(false);

  const updateStatus = () => {  // Prop to control login status
    setLogin(true);
  }

  return (
    <Router>
      <div className="App">
      <Header />
      <Routes>
        <Route path="/" element={<MultiForm updateStatus={updateStatus}/>}/>
        <Route path="/electives" element={isLoggedIn ? <Electives/> : <ErrorPage/>}/>
      </Routes>
      <Footer />
      </div>
    </Router>
  )
}

export default App;
