import { useState, useEffect, useRef } from 'react';
import { useI18n } from '../context/I18nContext';
import { calendar as calendarApi } from '../api/api';
import '../styles/calendar.css';

function getStatusClass(status) {
  const s = (status || '').toLowerCase();
  if (s.includes('\u0645\u062a\u0627\u062d') || s.includes('available')) return 'success';
  if (s.includes('\u0645\u063a\u0644\u0642') || s.includes('closed')) return 'danger';
  if (s.includes('\u0642\u0631\u064a\u0628') || s.includes('coming')) return 'info';
  return 'neutral';
}

function CalendarTable({ events, showHijri, showGreg, lang, t }) {
  if (!events || events.length === 0) {
    return (
      <table className="cal-table">
        <thead>
          <tr>
            <th>{t('cal.col.event')}</th>
            <th>{t('cal.col.status')}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan={2} style={{ textAlign: 'center', padding: 20, color: 'rgba(160,190,255,0.5)' }}>
              {t('cal.noData')}
            </td>
          </tr>
        </tbody>
      </table>
    );
  }

  return (
    <table className="cal-table">
      <thead>
        <tr>
          <th style={{ width: '30%' }}>{t('cal.col.event')}</th>
          {showHijri && <th>{t('cal.col.hijri_start')}</th>}
          {showHijri && <th>{t('cal.col.hijri_end')}</th>}
          {showGreg && <th>{t('cal.col.greg_start')}</th>}
          {showGreg && <th>{t('cal.col.greg_end')}</th>}
          <th style={{ width: '12%' }}>{t('cal.col.status')}</th>
        </tr>
      </thead>
      <tbody>
        {events.map((ev, i) => (
          <tr key={i}>
            <td>{ev.event}</td>
            {showHijri && <td>{ev.hijri_start}</td>}
            {showHijri && <td>{ev.hijri_end || '-'}</td>}
            {showGreg && <td>{ev.gregorian_start}</td>}
            {showGreg && <td>{ev.gregorian_end || '-'}</td>}
            <td>
              <span className={`status-badge ${getStatusClass(ev.status)}`}>{ev.status}</span>
