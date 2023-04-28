import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthBackground from '../components/AuthBackground';
import '../styles/auth-bg.css';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
