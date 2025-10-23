"use client";

import { createContext, useContext } from "react";

const StyleNonceContext = createContext<string | null>(null);

export const StyleNonceProvider = ({
  nonce,
  children,
}: {
  nonce: string | null;
  children: React.ReactNode;
}) => (
  <StyleNonceContext.Provider value={nonce}>
    {children}
  </StyleNonceContext.Provider>
);

export const useStyleNonce = () => useContext(StyleNonceContext);
