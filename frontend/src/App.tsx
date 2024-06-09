// import { useState } from 'react'
import React from 'react';
import './styles/App.scss'
import Header from './components/Header';
import Footer from './components/Footer';
import Form from './components/Form'

const App: React.FC = () => {

  return (
    <>
      <div className="App">
      <Header />
      <Form />
      <Footer />
      </div>
    </>
  )
}

export default App;
