import { io } from "socket.io-client";

const socket = io("http://localhost:8000");

export const subscribeToUpdates = (event, callback) => {
  socket.on(event, callback);
};

export const unsubscribeFromUpdates = (event) => {
  socket.off(event);
};
