import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { auth } from '../api/api';
import AuthBackground from '../components/AuthBackground';
import '../styles/auth-bg.css';

export default function OtpVerify() {
