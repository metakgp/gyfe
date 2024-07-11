import React from "react";

export interface UserObject {
  roll?: string;
  password?: string;
  securityQue?: string;
  securityAns?: string;
  isLoggedIn?: boolean;
}

// export const User: UserObject = {
//   roll: 'MyUserName',
//   password: 'John',
//   securityQue: 'john@doe.com',
//   securityAns: 'iwmk',
// }

const defaultState: AppState = {
  user: {
    isLoggedIn: false,
  },
  updateState: () => {},
};

export interface AppState {
  user?: UserObject;
  updateState: (newState: Partial<AppState>) => void;
}

export const UserContext = React.createContext<AppState>(defaultState);
