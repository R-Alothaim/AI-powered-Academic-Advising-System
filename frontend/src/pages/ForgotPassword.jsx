import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { auth } from '../api/api';
import AuthBackground from '../components/AuthBackground';
import '../styles/auth-bg.css';

export default function ForgotPassword() {
  const navigate = useNavigate();
