import io from 'socket.io-client';

const socket = io('http://localhost:5002');

socket.on('connect', () => {
  console.log('Connected');
  socket.emit('join_room', { room: 'execution_1' });
  socket.emit('start_execution', { testsuite_id: 1, room: 'execution_1' });
});

socket.on('execution_progress', (data) => {
  console.log(`Progress: ${data.progress}%`);
});