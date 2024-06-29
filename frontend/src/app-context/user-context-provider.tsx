import React, { useState } from 'react'
import { AppState, UserContext } from './user-context'

interface Props {
  children: React.ReactNode
}

export const UserContextProvider: React.FC<Props> = (props: Props): JSX.Element => {
 
  const [state, setState] = useState({})

  const updateState = (newState: Partial<AppState>) => {
    setState({ ...state, ...newState })
  }

  return (
    <UserContext.Provider value={{ ...state, updateState }}>{props.children}</UserContext.Provider>
  )
}