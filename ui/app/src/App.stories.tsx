import type { Meta, StoryObj } from '@storybook/react-vite'
import App from './App'

const meta = {
  title: 'RQU-UI-03/UI基盤Smoke',
  component: App,
  parameters: { layout: 'fullscreen' },
  tags: ['autodocs'],
} satisfies Meta<typeof App>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {}

