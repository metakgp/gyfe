// import { useState } from 'react'
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import './styles/App.scss'
import Header from './components/Header'
import Footer from './components/Footer'
import Form from './components/Form'
import Login from './components/Login'
import Electives from './components/Electives';

const App: React.FC = () => {

  return (
    <Router>
      <div className="App">
      <Header />
      <Routes>
        <Route path="/" element={<Form/>}/>
        <Route path="/login" element={<Login/>}/>
        <Route path="/electives" element={<Electives/>}/>
      </Routes>
      <Footer />
      </div>
    </Router>
  )
}

export default App;
