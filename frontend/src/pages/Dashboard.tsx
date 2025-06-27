import React from 'react'

export default function Dashboard() {
    return(
        <div className='min-h-screen p-6 pl-16 bg-slate-100'>
            <header className='mb-6'>
                <h1 className='text-3xl font-bold text-blue-700'>Legal Guard Dashboard</h1>
            </header>

            <section className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-6'>
                <div className='bg-white p-4 rounded shadow'>Contracts Analyzed: <strong>--</strong></div>
                <div className='bg-white p-4 rounded shadow'>Compliance Rate: <strong>--%</strong></div>
                <div className='bg-white p-4 rounded shadow'>ALerts Detected: <strong>--</strong></div>
            </section>

            <section className='mb-6'>
                <h2 className='text-xl font-semibold mb-2'>Recent Activity</h2>
                <div className='bg-white p-4 rounded shadow'></div>
            </section>

            <section className='flex gap-4'>
                <button className='bg-blue-600 text-white px-4 py-2 rounded'>Upload Contract</button>
                <button className='bg-gray-700 text-white px-4 py-2 rounded'>View Reports</button>
            </section>
        </div>
    )
}