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
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function TabSection({ label, tabs, showHijri, showGreg, lang, t }) {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <section className="tabs" aria-label={label}>
      <div className="tablist" role="tablist">
        {tabs.map((tab, i) => (
          <button
            key={i}
            className={`tab${activeTab === i ? ' active' : ''}`}
            role="tab"
            aria-selected={activeTab === i}
            onClick={() => setActiveTab(i)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {tabs.map((tab, i) => (
        <div key={i} className={`tabpanel${activeTab === i ? ' active' : ''}`} role="tabpanel">
          <CalendarTable events={tab.events} showHijri={showHijri} showGreg={showGreg} lang={lang} t={t} />
        </div>
      ))}
    </section>
  );
}

export default function Calendar() {
  const { lang, t } = useI18n();
  const [year, setYear] = useState('1447');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showHijri, setShowHijri] = useState(true);
  const [showGreg, setShowGreg] = useState(true);
  const [lastUpdate, setLastUpdate] = useState('');
  const printBtnRef = useRef(null);
