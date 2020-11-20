import React, { useState } from 'react';

import logoImg from '../../assets/logo.png';

import api from '../../services/api';

import styles from './Main.module.scss';
 
export default function Main() {
    const [ id, setId ] = useState('');

    async function handleLogon(e) {
        e.preventDefault();

        try {
            const response = await api.post('session', { id });
            
        } catch (err) {
            alert('Falha ao efetuar busca, favor tentar novamente');
        }

    }

    return (
        <div className={styles["container"]}>
            <section className={styles["form"]}>
                <img src={logoImg} alt="Buscador"/>

                <form onSubmit={handleLogon}>
                    <h1>Faça sua busca</h1>

                    <input 
                        placeholder="Sua Busca"
                        value={id}
                        onChange={e => setId(e.target.value)}
                    />
                    <button className="button" type="submit">Buscar</button>
                </form>
            </section>
        </div>
    );
}